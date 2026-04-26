# service/dynamic_profit_recheck_service.py
# -*- coding: utf-8 -*-
"""
动态止盈撤单后重新判定服务（简化版，使用上下文）
"""
from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
from domain.day_data import DayData
from domain.stores import SessionRegistry
from service.order_executor import place_sell, sell_qty_by_percent
from config.strategy import (
    MAX_DYNAMIC_PROFIT_SELL_TIMES,
    CONDITION2_DECLINE_PERCENT,
    CONDITION2_SELL_PRICE_OFFSET,
    CONDITION2_DYNAMIC_LINE_THRESHOLD,
    CONDITION2_SELL_PERCENT_HIGH,
    CONDITION2_SELL_PERCENT_LOW,
    MAX_CONDITION9_SELL_TIMES,
    CONDITION9_DECLINE_PERCENT,
    CONDITION9_SELL_PRICE_OFFSET,
    CONDITION9_DYNAMIC_LINE_THRESHOLD,
    CONDITION9_SELL_PERCENT_HIGH,
    CONDITION9_SELL_PERCENT_LOW,
)

def execute_post_cancel_recheck(
    symbol: str,
    current_price: float,
    available_position: int,
    day_data: DayData,
    base_price: float,
    board_break_active: bool,
    session_registry: SessionRegistry
) -> Tuple[bool, bool]:
    """重新判定撤单后的条件2和条件9，返回 (c2_processed, c9_processed)"""
    ctx2 = session_registry.get_condition2(symbol)
    ctx9 = session_registry.get_condition9(symbol, base_price)

    c2_processed = False
    c9_processed = False

    # 条件2 重判定
    if getattr(ctx2, '_recheck_after_cancel', False):
        ctx2._recheck_after_cancel = False
        if ctx2.dynamic_profit_triggered and ctx2.dynamic_profit_sell_times < MAX_DYNAMIC_PROFIT_SELL_TIMES and available_position > 0:
            profit_line = ctx2.dynamic_profit_line
            if current_price <= profit_line:
                dynamic_line_increase = (profit_line - base_price) / base_price if base_price > 0 else 0
                sell_percent = CONDITION2_SELL_PERCENT_HIGH if dynamic_line_increase >= CONDITION2_DYNAMIC_LINE_THRESHOLD else CONDITION2_SELL_PERCENT_LOW
                qty = sell_qty_by_percent(available_position, sell_percent)
                if qty > 0:
                    place_sell(symbol, current_price - CONDITION2_SELL_PRICE_OFFSET, qty,
                               "条件2动态止盈撤单后重新判定", "condition2", {},
                               session_registry=session_registry)
                    ctx2.dynamic_profit_sell_times += 1
                    ctx2.condition2_triggered_and_sold = True
                    c2_processed = True
                    # 清理条件9
                    ctx9.condition9_triggered = False
                    ctx9.condition9_high_price = -float('inf')
                    ctx9.condition9_profit_line = -float('inf')
            elif current_price > ctx2.dynamic_profit_high_price:
                ctx2.dynamic_profit_high_price = current_price
                ctx2.dynamic_profit_line = current_price * (1 - CONDITION2_DECLINE_PERCENT)
                c2_processed = True

    # 条件9 重判定
    if not c2_processed and getattr(ctx9, '_recheck_after_cancel', False):
        ctx9._recheck_after_cancel = False
        if ctx9.condition9_triggered and ctx9.condition9_sell_times < MAX_CONDITION9_SELL_TIMES and available_position > 0:
            profit_line = ctx9.condition9_profit_line
            if current_price <= profit_line:
                dynamic_line_increase = (profit_line - base_price) / base_price if base_price > 0 else 0
                sell_percent = CONDITION9_SELL_PERCENT_HIGH if dynamic_line_increase >= CONDITION9_DYNAMIC_LINE_THRESHOLD else CONDITION9_SELL_PERCENT_LOW
                qty = sell_qty_by_percent(available_position, sell_percent)
                if qty > 0:
                    place_sell(symbol, current_price - CONDITION9_SELL_PRICE_OFFSET, qty,
                               "条件9动态止盈撤单后重新判定", "condition9", {},
                               session_registry=session_registry)
                    ctx9.condition9_sell_times += 1
                    c9_processed = True
            elif current_price > ctx9.condition9_high_price:
                ctx9.condition9_high_price = current_price
                ctx9.condition9_profit_line = current_price * (1 - CONDITION9_DECLINE_PERCENT)
                c9_processed = True

    return c2_processed, c9_processed