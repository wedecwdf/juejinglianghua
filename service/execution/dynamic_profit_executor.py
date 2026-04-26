# service/execution/dynamic_profit_executor.py
# -*- coding: utf-8 -*-
"""条件2和条件9动态止盈执行器"""
from __future__ import annotations
from domain.day_data import DayData
from domain.contexts.condition2 import Condition2Context
from domain.contexts.condition9 import Condition9Context
from domain.stores import SessionRegistry
from service.condition_service import check_condition2, check_condition9
from service.order_executor import place_sell, sell_qty_by_percent

def execute_condition2_profit(symbol: str, current_price: float,
                              available_position: int, day_data: DayData,
                              base_price: float, board_break_active: bool,
                              session_registry: SessionRegistry) -> bool:
    context = session_registry.get_condition2(symbol)
    increase = (current_price - base_price) / base_price if base_price > 0 else 0
    res = check_condition2(day_data, increase, current_price, base_price, context, board_break_active)
    if res:
        qty = sell_qty_by_percent(available_position, res["sell_percent"])
        if qty:
            place_sell(symbol, current_price - res["sell_price_offset"], qty,
                       res["reason"], "condition2", res["trigger_data"],
                       session_registry=session_registry)
            context.dynamic_profit_sell_times += 1
            # 更新总的卖出次数（暂存于 DayData 或 session_registry 中的计数器）
            session_registry._gw.total_sell_times = session_registry._gw.total_sell_times.get(symbol, 0) + 1
            context.condition2_triggered_and_sold = True
            # 清理条件9
            context9 = session_registry.get_condition9(symbol, base_price)
            context9.condition9_triggered = False
            context9.condition9_high_price = -float('inf')
            context9.condition9_profit_line = -float('inf')
            return True
    return False

def execute_condition9_profit(symbol: str, current_price: float,
                              available_position: int, day_data: DayData,
                              base_price: float, board_break_active: bool,
                              condition2_active: bool,
                              session_registry: SessionRegistry) -> bool:
    context = session_registry.get_condition9(symbol, base_price)
    increase = (current_price - base_price) / base_price if base_price > 0 else 0
    res = check_condition9(day_data, increase, current_price, base_price, context, board_break_active, condition2_active)
    if res:
        qty = sell_qty_by_percent(available_position, res["sell_percent"])
        if qty:
            place_sell(symbol, current_price - res["sell_price_offset"], qty,
                       res["reason"], "condition9", res["trigger_data"],
                       session_registry=session_registry)
            context.condition9_sell_times += 1
            session_registry._gw.total_sell_times = session_registry._gw.total_sell_times.get(symbol, 0) + 1
            return True
    return False