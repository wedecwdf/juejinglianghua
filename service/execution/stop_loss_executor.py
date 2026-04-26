# service/execution/stop_loss_executor.py
# -*- coding: utf-8 -*-
"""
次日固定止损执行器（Layer 1）
"""
from __future__ import annotations
from typing import Optional
from domain.day_data import DayData
from domain.stores import SessionRegistry
from service.day_adjust_service import check_dynamic_profit_next_day_adjustment
from service.order_executor import place_sell

def execute_next_day_stop_loss(symbol: str, current_price: float,
                               available_position: int, day_data: DayData,
                               session_registry: SessionRegistry) -> bool:
    sell_qty = check_dynamic_profit_next_day_adjustment(day_data, current_price, available_position)
    if sell_qty:
        place_sell(symbol, current_price, sell_qty,
                   "动态止盈次日调整机制止损", "dynamic_profit_next_day_adjustment", {},
                   session_registry=session_registry)
        return True
    return False