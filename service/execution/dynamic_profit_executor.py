# service/execution/dynamic_profit_executor.py
# -*- coding: utf-8 -*-
"""
条件2和条件9动态止盈执行器（Layer 4/5）
"""
from __future__ import annotations
from domain.day_data import DayData
from domain.stores import SessionRegistry
from service.condition_service import check_condition2, check_condition9
from service.order_executor import place_sell, sell_qty_by_percent

def execute_condition2_profit(symbol: str, current_price: float,
                              available_position: int, day_data: DayData,
                              base_price: float, board_break_active: bool,
                              session_registry: SessionRegistry) -> bool:
    res = check_condition2(day_data, (current_price - base_price) / base_price if base_price > 0 else 0,
                           current_price, base_price, board_break_active=board_break_active)
    if res:
        qty = sell_qty_by_percent(available_position, res["sell_percent"])
        if qty:
            place_sell(symbol, current_price - res["sell_price_offset"], qty,
                       res["reason"], "condition2", res["trigger_data"],
                       session_registry=session_registry)
            day_data.dynamic_profit_sell_times += 1
            day_data.total_sell_times += 1
            day_data.condition2_triggered_and_sold = True
            if day_data.condition9_triggered:
                day_data.condition9_triggered = False
                day_data.condition9_high_price = -float('inf')
                day_data.condition9_profit_line = -float('inf')
                print(f"【优先级覆盖】{symbol} 条件2触发并执行，清理条件9状态")
            return True
    return False

def execute_condition9_profit(symbol: str, current_price: float,
                              available_position: int, day_data: DayData,
                              base_price: float, board_break_active: bool,
                              condition2_active: bool,
                              session_registry: SessionRegistry) -> bool:
    res = check_condition9(day_data, (current_price - base_price) / base_price if base_price > 0 else 0,
                           current_price, base_price, board_break_active=board_break_active,
                           condition2_active=condition2_active)
    if res:
        qty = sell_qty_by_percent(available_position, res["sell_percent"])
        if qty:
            place_sell(symbol, current_price - res["sell_price_offset"], qty,
                       res["reason"], "condition9", res["trigger_data"],
                       session_registry=session_registry)
            day_data.condition9_sell_times += 1
            day_data.total_sell_times += 1
            return True
    return False