# service/order_executor.py
# -*- coding: utf-8 -*-
"""
订单执行服务，不再提供默认仓库实例，必须由调用者注入。
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Dict, Any
import pytz
from repository.gm_data_source import place_order
from repository.mail_sender import send_email
from config.account import ACCOUNT_ID
from config.strategy import (
    CONDITION8_SELL_QUANTITY, CONDITION8_BUY_QUANTITY,
    CONDITION8_RISE_PERCENT, CONDITION8_DECLINE_PERCENT,
    CONDITION8_HIGH_FREQ_RISE_PERCENT, CONDITION8_HIGH_FREQ_DECLINE_PERCENT,
    CONDITION8_LOW_FREQ_RISE_PERCENT, CONDITION8_LOW_FREQ_DECLINE_PERCENT,
    HIGH_FREQUENCY_STOCKS, LOW_FREQUENCY_STOCKS,
    CONDITION8_MULTIPLE_ORDER_ENABLED
)
from domain.stores.base import AbstractOrderLedger, AbstractSessionRegistry

logger = logging.getLogger(__name__)
beijing_tz = pytz.timezone("Asia/Shanghai")

def place_sell(symbol: str, price: float, quantity: int,
               reason: str, condition_type: str, trigger_data: Dict[str, Any],
               order_ledger: AbstractOrderLedger,
               session_registry: AbstractSessionRegistry) -> None:
    cl_ord_id = place_order(symbol, price, quantity, side=2, position_effect=2, account=ACCOUNT_ID)
    if not cl_ord_id:
        return

    order_data = {
        "symbol": symbol,
        "price": price,
        "quantity": quantity,
        "side": "卖出",
        "reason": reason,
        "created_at": datetime.now(beijing_tz),
        "status": "已委托",
        "condition_type": condition_type,
        "trigger_data": trigger_data,
        "account_id": ACCOUNT_ID
    }

    if trigger_data and trigger_data.get("is_multiple_order"):
        multiple_info = trigger_data.get("multiple_order_info", {})
        order_data["is_multiple_order"] = True
        order_data["base_quantity"] = multiple_info.get("base_quantity", quantity)
        order_data["actual_multiple"] = multiple_info.get("actual_multiple", 1)
        order_data["skipped_grids"] = multiple_info.get("skipped_grids", 0)
        order_data["hit_limit"] = multiple_info.get("hit_limit", False)

    if trigger_data and trigger_data.get("threshold_info"):
        threshold_info = trigger_data.get("threshold_info", {})
        order_data["stock_type"] = threshold_info.get("stock_type", "default")
        order_data["rise_threshold_used"] = threshold_info.get("rise_threshold_used", CONDITION8_RISE_PERCENT)
        order_data["decline_threshold_used"] = threshold_info.get("decline_threshold_used", CONDITION8_DECLINE_PERCENT)

    order_ledger.add_pending_order(cl_ord_id, order_data)

    if condition_type == "condition8":
        day_data = session_registry.get(symbol)
        if day_data:
            ctx8 = session_registry.get_condition8(symbol, day_data.base_price)
            ctx8.condition8_last_trade_price = price
            ctx8.condition8_sell_triggered_for_current_ref = True
            current_ref = trigger_data.get('current_ref_price', ctx8.condition8_reference_price)
            logger.info("【条件8挂单】%s 卖出委托 %.4f 已记录，基准价 %.4f 下卖出挂单状态已标记", symbol, price, current_ref)

        if trigger_data and trigger_data.get("is_multiple_order"):
            mult_info = trigger_data.get("multiple_order_info", {})
            logger.info("【条件8倍数委托详情】%s 基础数量:%d 实际倍数:%d 跳过网格:%d 网格间隔:%.2f%%",
                        symbol, mult_info.get('base_quantity'), mult_info.get('actual_multiple'),
                        mult_info.get('skipped_grids'), mult_info.get('grid_interval_percent', 0) * 100)
        if trigger_data and trigger_data.get("threshold_info"):
            thr_info = trigger_data.get("threshold_info", {})
            type_desc = "高频" if thr_info.get('stock_type') == 'high' else ("低频" if thr_info.get('stock_type') == 'low' else "默认")
            logger.info("【条件8独立阈值详情】%s 类型:%s 上涨阈值:%.2f%% 下跌阈值:%.2f%%",
                        symbol, type_desc, thr_info.get('rise_threshold_used', 0) * 100,
                        thr_info.get('decline_threshold_used', 0) * 100)

    logger.info("【交易执行】%s 卖出：%d股 @ %.4f，原因：%s", symbol, quantity, price, reason)

def place_buy(symbol: str, price: float, quantity: int,
              reason: str, condition_type: str, trigger_data: Dict[str, Any],
              order_ledger: AbstractOrderLedger,
              session_registry: AbstractSessionRegistry) -> None:
    cl_ord_id = place_order(symbol, price, quantity, side=1, position_effect=1, account=ACCOUNT_ID)
    if not cl_ord_id:
        return

    order_data = {
        "symbol": symbol,
        "price": price,
        "quantity": quantity,
        "side": "买入",
        "reason": reason,
        "created_at": datetime.now(beijing_tz),
        "status": "已委托",
        "condition_type": condition_type,
        "trigger_data": trigger_data,
        "account_id": ACCOUNT_ID
    }

    if trigger_data and trigger_data.get("is_multiple_order"):
        multiple_info = trigger_data.get("multiple_order_info", {})
        order_data["is_multiple_order"] = True
        order_data["base_quantity"] = multiple_info.get("base_quantity", quantity)
        order_data["actual_multiple"] = multiple_info.get("actual_multiple", 1)
        order_data["skipped_grids"] = multiple_info.get("skipped_grids", 0)
        order_data["hit_limit"] = multiple_info.get("hit_limit", False)

    if trigger_data and trigger_data.get("threshold_info"):
        threshold_info = trigger_data.get("threshold_info", {})
        order_data["stock_type"] = threshold_info.get("stock_type", "default")
        order_data["rise_threshold_used"] = threshold_info.get("rise_threshold_used", CONDITION8_RISE_PERCENT)
        order_data["decline_threshold_used"] = threshold_info.get("decline_threshold_used", CONDITION8_DECLINE_PERCENT)

    order_ledger.add_pending_order(cl_ord_id, order_data)

    if condition_type == "condition8":
        day_data = session_registry.get(symbol)
        if day_data:
            ctx8 = session_registry.get_condition8(symbol, day_data.base_price)
            ctx8.condition8_last_trade_price = price
            ctx8.condition8_buy_triggered_for_current_ref = True
            current_ref = trigger_data.get('current_ref_price', ctx8.condition8_reference_price)
            logger.info("【条件8挂单】%s 买入委托 %.4f 已记录，基准价 %.4f 下买入挂单状态已标记", symbol, price, current_ref)

        if trigger_data and trigger_data.get("is_multiple_order"):
            mult_info = trigger_data.get("multiple_order_info", {})
            logger.info("【条件8倍数委托详情】%s 基础数量:%d 实际倍数:%d 跳过网格:%d 网格间隔:%.2f%%",
                        symbol, mult_info.get('base_quantity'), mult_info.get('actual_multiple'),
                        mult_info.get('skipped_grids'), mult_info.get('grid_interval_percent', 0) * 100)
        if trigger_data and trigger_data.get("threshold_info"):
            thr_info = trigger_data.get("threshold_info", {})
            type_desc = "高频" if thr_info.get('stock_type') == 'high' else ("低频" if thr_info.get('stock_type') == 'low' else "默认")
            logger.info("【条件8独立阈值详情】%s 类型:%s 上涨阈值:%.2f%% 下跌阈值:%.2f%%",
                        symbol, type_desc, thr_info.get('rise_threshold_used', 0) * 100,
                        thr_info.get('decline_threshold_used', 0) * 100)

    logger.info("【交易执行】%s 买入：%d股 @ %.4f，原因：%s", symbol, quantity, price, reason)

def sell_qty_by_percent(available: int, percent: float) -> int:
    qty = int(available * percent)
    return (qty // 100) * 100