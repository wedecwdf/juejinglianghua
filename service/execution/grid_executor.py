# service/execution/grid_executor.py
# -*- coding: utf-8 -*-
"""
条件8动态基准价网格交易执行器（Layer 7）
"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.stores import OrderLedger, SessionRegistry
from service.condition_service import check_condition8
from service.order_executor import place_sell, place_buy
from config.strategy import (
    CONDITION8_MAX_TOTAL_QUANTITY,
    CONDITION8_MULTIPLE_ORDER_ENABLED
)

logger = logging.getLogger(__name__)

def execute_condition8_grid(symbol: str, current_price: float,
                            available_position: int, day_data: DayData,
                            base_price: float,
                            order_ledger: OrderLedger,
                            session_registry: SessionRegistry) -> bool:
    context = session_registry.get_condition8(symbol, base_price)
    res = check_condition8(day_data, context, current_price, available_position, order_ledger=order_ledger)
    if not res:
        return False

    total_sell_today = context.condition8_total_sell_today
    total_buy_today = context.condition8_total_buy_today
    max_total = CONDITION8_MAX_TOTAL_QUANTITY.get(symbol, 0)

    qty = res["quantity"]
    side = res["side"]
    base_qty = res.get("base_quantity", qty)
    actual_multiple = res.get("actual_multiple", 1)
    stock_type = res.get("stock_type", "default")
    rise_thr = res.get("rise_threshold", 0)
    decline_thr = res.get("decline_threshold", 0)

    if side == "sell":
        if total_sell_today + qty > max_total:
            logger.info("[条件8卖出-独立阈值] %s 累计卖出%d+%d将超过上限%d，跳过",
                        symbol, total_sell_today, qty, max_total)
            return True
        type_desc = "高频" if stock_type == "high" else ("低频" if stock_type == "low" else "默认")
        logger.info("【条件8独立阈值执行】%s 类型:%s 上涨阈值:%.2f%% 下跌阈值:%.2f%%",
                    symbol, type_desc, rise_thr * 100, decline_thr * 100)
        place_sell(symbol, current_price, qty, res["reason"], "condition8", res["trigger_data"],
                   order_ledger=order_ledger, session_registry=session_registry)
        context.condition8_trade_times += 1
        context.condition8_last_trade_price = current_price
        context.condition8_last_trigger_price = current_price
        context.condition8_total_sell_today = total_sell_today + qty
        if CONDITION8_MULTIPLE_ORDER_ENABLED and actual_multiple > 1:
            logger.info("【条件8倍数委托执行】%s 卖出 %d股 (基础%d×倍数%d)", symbol, qty, base_qty, actual_multiple)
        return True
    else:
        if total_buy_today + qty > max_total:
            logger.info("[条件8买入-独立阈值] %s 累计买入%d+%d将超过上限%d，跳过",
                        symbol, total_buy_today, qty, max_total)
            return True
        type_desc = "高频" if stock_type == "high" else ("低频" if stock_type == "low" else "默认")
        logger.info("【条件8独立阈值执行】%s 类型:%s 上涨阈值:%.2f%% 下跌阈值:%.2f%%",
                    symbol, type_desc, rise_thr * 100, decline_thr * 100)
        place_buy(symbol, current_price, qty, res["reason"], "condition8", res["trigger_data"],
                  order_ledger=order_ledger, session_registry=session_registry)
        context.condition8_trade_times += 1
        context.condition8_last_trade_price = current_price
        context.condition8_last_trigger_price = current_price
        context.condition8_total_buy_today = total_buy_today + qty
        if CONDITION8_MULTIPLE_ORDER_ENABLED and actual_multiple > 1:
            logger.info("【条件8倍数委托执行】%s 买入 %d股 (基础%d×倍数%d)", symbol, qty, base_qty, actual_multiple)
        return True