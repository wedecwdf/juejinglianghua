# service/execution/pyramid_profit_executor.py
# -*- coding: utf-8 -*-
"""金字塔止盈执行器"""
from __future__ import annotations
from domain.day_data import DayData
from domain.stores import SessionRegistry
from service.conditions import check_pyramid_profit
from service.order_executor import place_sell
from config.strategy import PYRAMID_PROFIT_SELL_PRICE_OFFSET

def execute_pyramid_profit(symbol: str, current_price: float,
                           available_position: int, day_data: DayData,
                           session_registry: SessionRegistry) -> bool:
    if available_position <= 0:
        return False
    context = session_registry.get_pyramid(symbol, day_data.base_price)
    res = check_pyramid_profit(symbol, context, current_price, available_position)
    if res:
        qty = res["quantity"]
        place_sell(symbol, current_price - PYRAMID_PROFIT_SELL_PRICE_OFFSET, qty,
                   res["reason"], "pyramid_profit", res["trigger_data"],
                   session_registry=session_registry)
        context.pyramid_profit_status[res["trigger_data"]["pyramid_level"]] = True
        context.pyramid_profit_triggered = True
        return True
    return False