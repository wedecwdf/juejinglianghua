# adapter/gm_adapter.py
# -*- coding: utf-8 -*-
"""
统一封装所有 GM API 调用，作为外部服务适配器。
合并了原 context_wrapper 中的 subscribe、history_data、get_position 等接口。
"""

from __future__ import annotations
import logging
from datetime import timedelta, date
from typing import Any, List, Dict, Optional

from gm.api import (
    history,
    ADJUST_PREV,
    subscribe as gm_subscribe,
    history as gm_history,
    get_position as gm_get_position,
    get_cash as gm_get_cash,
    get_orders as gm_get_orders,
    order_cancel as gm_order_cancel,
    order_volume as gm_order_volume,
    get_trading_dates as gm_get_trading_dates,
)

from config.account import ACCOUNT_ID

logger = logging.getLogger(__name__)

LIMIT_ORDER_TYPE = 1

# ---------------------------------------------------------------------------
# 原 context_wrapper 中的被动转发函数
# ---------------------------------------------------------------------------

def subscribe(symbols: List[str], frequency: str, count: int, wait_group: bool = False) -> None:
    gm_subscribe(symbols=symbols, frequency=frequency, count=count, wait_group=wait_group)


def history_data(symbol: str, frequency: str, start_time: str, end_time: str,
                 fields: str = "", adjust: int = 0, df: bool = False) -> Any:
    return gm_history(symbol=symbol, frequency=frequency,
                      start_time=start_time, end_time=end_time,
                      fields=fields, adjust=adjust, df=df)


def get_position() -> List[Dict[str, Any]]:
    return gm_get_position()


def get_cash() -> Dict[str, Any]:
    return gm_get_cash()


def get_orders() -> List[Dict[str, Any]]:
    return gm_get_orders()


def cancel_order_by_cl_ord_id(cl_ord_id: str) -> None:
    gm_order_cancel(wait_cancel_orders=[{"cl_ord_id": cl_ord_id}])


def order_volume(symbol: str, volume: int, side: int, order_type: int,
                 position_effect: int, price: float) -> Optional[str]:
    orders = gm_order_volume(symbol=symbol, volume=volume, side=side,
                             order_type=order_type, position_effect=position_effect,
                             price=price)
    return orders[0]["cl_ord_id"] if orders else None


def get_trading_dates(start_date: str, end_date: str) -> List[str]:
    return gm_get_trading_dates(exchange="SHSE", start_date=start_date, end_date=end_date)


# ---------------------------------------------------------------------------
# 原有 gm_adapter 中的业务级封装
# ---------------------------------------------------------------------------

def load_history_data(symbol: str, end_date: date, max_history_days: int) -> Optional[Any]:
    """获取历史日线数据，返回 DataFrame。天数由调用者提供"""
    try:
        start_date = (end_date - timedelta(days=max_history_days)).strftime("%Y-%m-%d")
        end_str = (end_date - timedelta(days=1)).strftime("%Y-%m-%d")
        df = history(
            symbol=symbol, frequency="1d",
            start_time=start_date, end_time=end_str,
            fields="symbol,eob,open,high,low,close,volume",
            adjust=ADJUST_PREV, df=True
        )
        if not df.empty:
            df["date"] = df["eob"].dt.date
            df.set_index("date", inplace=True)
            return df
        return None
    except Exception as e:
        logger.warning("加载 %s 历史数据失败: %s", symbol, e)
        return None


def get_available_position(symbol: str) -> int:
    try:
        positions = get_position()
        for pos in positions:
            if pos["symbol"] == symbol and pos["side"] == 1:
                return int(pos.get("available", 0))
        return 0
    except Exception as e:
        logger.warning("获取 %s 可用持仓失败: %s", symbol, e)
        return 0


def fetch_cash() -> Optional[Dict[str, Any]]:
    try:
        return get_cash()
    except Exception as e:
        logger.warning("获取资金信息失败: %s", e)
        return None


def fetch_positions() -> List[Dict[str, Any]]:
    try:
        return get_position()
    except Exception as e:
        logger.warning("获取持仓失败: %s", e)
        return []


def fetch_orders() -> List[Dict[str, Any]]:
    try:
        return get_orders()
    except Exception as e:
        logger.warning("获取订单列表失败: %s", e)
        return []


def place_order(symbol: str, price: float, volume: int, side: int,
                position_effect: int, account: str = None) -> Optional[str]:
    """下单，返回 cl_ord_id"""
    if account is None:
        account = ACCOUNT_ID
    if not account:
        logger.error("【致命错误】ACCOUNT_ID 为空，无法下单")
        return None
    try:
        orders = gm_order_volume(
            symbol=symbol, volume=volume, side=side,
            order_type=LIMIT_ORDER_TYPE, position_effect=position_effect,
            price=price, account=account
        )
        return orders[0]["cl_ord_id"] if orders else None
    except Exception as e:
        logger.error("【下单失败】%s: %s", symbol, e)
        return None


def cancel_order(cl_ord_id: str, account_id: Optional[str] = None) -> None:
    try:
        param = {"cl_ord_id": cl_ord_id}
        if account_id and account_id != "":
            param["account_id"] = account_id
            logger.info("【撤单】%s 使用账户ID: %s", cl_ord_id, account_id)
        else:
            logger.info("【撤单】%s 账户ID为空，尝试使用默认账户", cl_ord_id)
        gm_order_cancel(wait_cancel_orders=[param])
        logger.info("【撤单成功】%s", cl_ord_id)
    except Exception as e:
        logger.warning("撤单失败: %s", e)
        if "account_id" in str(e).lower() and account_id is not None:
            logger.info("【重试撤单】去掉 account_id 再次撤 %s", cl_ord_id)
            gm_order_cancel(wait_cancel_orders=[{"cl_ord_id": cl_ord_id}])