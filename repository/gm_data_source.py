# repository/gm_data_source.py
# -*- coding: utf-8 -*-
"""
统一封装所有 GM API 调用，便于 mock 与单测
"""
from __future__ import annotations
import logging
from datetime import timedelta, date
from typing import Any, List, Dict, Optional
from gm.api import (
    history, ADJUST_PREV, get_position, get_cash, get_orders, order_cancel,
    order_volume, get_trading_dates as gm_get_trading_dates
)
from config.account import ACCOUNT_ID
from config.strategy import MAX_HISTORY_DAYS
from config.calendar import TRADING_HOURS

logger = logging.getLogger(__name__)
OrderType_Limit = 1


def load_history_data(symbol: str, end_date: date) -> Optional[Any]:
    try:
        start_date = (end_date - timedelta(days=MAX_HISTORY_DAYS)).strftime("%Y-%m-%d")
        end_str = (end_date - timedelta(days=1)).strftime("%Y-%m-%d")
        df = history(
            symbol=symbol,
            frequency="1d",
            start_time=start_date,
            end_time=end_str,
            fields="symbol,eob,open,high,low,close,volume",
            adjust=ADJUST_PREV,
            df=True
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
        from gm.api import get_position as gm_get_position
        positions = gm_get_position()
        for pos in positions:
            if pos["symbol"] == symbol and pos["side"] == 1:
                return int(pos.get("available", 0))
        return 0
    except Exception as e:
        logger.warning("获取 %s 可用持仓失败: %s", symbol, e)
        return 0


def get_cash() -> Optional[Dict[str, Any]]:
    try:
        from gm.api import get_cash as gm_get_cash
        return gm_get_cash()
    except Exception as e:
        logger.warning("获取资金信息失败: %s", e)
        return None


def get_position() -> List[Dict[str, Any]]:
    try:
        from gm.api import get_position as gm_get_position
        return gm_get_position()
    except Exception as e:
        logger.warning("获取持仓失败: %s", e)
        return []


def get_orders() -> List[Dict[str, Any]]:
    try:
        from gm.api import get_orders as gm_get_orders
        return gm_get_orders()
    except Exception as e:
        logger.warning("获取订单列表失败: %s", e)
        return []


def cancel_order(cl_ord_id: str, account_id: Optional[str] = None) -> None:
    try:
        from gm.api import order_cancel as gm_order_cancel
        param = {"cl_ord_id": cl_ord_id}
        if account_id is not None and account_id != "":
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
        else:
            raise


def place_order(symbol: str, price: float, volume: int, side: int,
                position_effect: int, account: str) -> Optional[str]:
    try:
        from gm.api import order_volume as gm_order_volume
        if not account:
            logger.error("【致命错误】ACCOUNT_ID 为空，无法下单")
            return None
        orders = gm_order_volume(
            symbol=symbol,
            volume=volume,
            side=side,
            order_type=OrderType_Limit,
            position_effect=position_effect,
            price=price,
            account=account
        )
        return orders[0]["cl_ord_id"] if orders else None
    except Exception as e:
        logger.error("【下单失败】%s: %s", symbol, e)
        return None


def get_trading_dates(start_date: str, end_date: str) -> List[str]:
    try:
        return gm_get_trading_dates(exchange="SHSE", start_date=start_date, end_date=end_date)
    except Exception as e:
        logger.warning("获取交易日列表失败: %s", e)
        return []