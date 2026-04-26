# service/conditions/cond9.py
# -*- coding: utf-8 -*-
"""
条件9：第一区间动态止盈（直接操作 Condition9Context）
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.contexts.condition9 import Condition9Context
from config.strategy import (
    CONDITION9_ENABLED,
    MAX_CONDITION9_SELL_TIMES,
    CONDITION9_UPPER_BAND_PERCENT,
    CONDITION9_LOWER_BAND_PERCENT,
    CONDITION9_TRIGGER_PERCENT,
    CONDITION9_DECLINE_PERCENT,
    CONDITION9_SELL_PRICE_OFFSET,
    CONDITION9_DYNAMIC_LINE_THRESHOLD,
    CONDITION9_SELL_PERCENT_HIGH,
    CONDITION9_SELL_PERCENT_LOW,
)
from .utils import _check_dynamic_profit_core

def check_condition9(
    context: Condition9Context,
    increase: float,
    current_price: float,
    base_price: float,
    board_break_active: bool = False,
    condition2_active: bool = False
) -> Optional[Dict[str, Any]]:
    # 条件9特有的价格区间停止检查
    if context.condition9_stopped:
        return None
    upper_band = context.condition9_upper_band
    lower_band = context.condition9_lower_band
    if current_price > upper_band:
        context.condition9_stopped = True
        context.condition9_triggered = False
        print(f'【条件9停止监测】价格突破区间上限，停止监测')
        return None
    if not (lower_band <= current_price <= upper_band):
        return None

    # 条件2优先级检查
    def _priority_check():
        if condition2_active:
            if context.condition9_triggered:
                context.condition9_triggered = False
                context.condition9_high_price = -float('inf')
                context.condition9_profit_line = -float('inf')
                print(f"【优先级覆盖】条件二激活，条件九状态被清理")
            return True
        return False

    return _check_dynamic_profit_core(
        context=context,
        increase=increase,
        current_price=current_price,
        base_price=base_price,
        enabled=CONDITION9_ENABLED,
        max_sell_times=MAX_CONDITION9_SELL_TIMES,
        trigger_percent=CONDITION9_TRIGGER_PERCENT,
        decline_percent=CONDITION9_DECLINE_PERCENT,
        sell_price_offset=CONDITION9_SELL_PRICE_OFFSET,
        dynamic_line_threshold=CONDITION9_DYNAMIC_LINE_THRESHOLD,
        sell_percent_high=CONDITION9_SELL_PERCENT_HIGH,
        sell_percent_low=CONDITION9_SELL_PERCENT_LOW,
        condition_name='条件9',
        board_break_active=board_break_active,
        priority_check_fn=_priority_check,
        get_triggered=lambda c: c.condition9_triggered,
        set_triggered=lambda c, v: setattr(c, 'condition9_triggered', v),
        get_high_price=lambda c: c.condition9_high_price,
        set_high_price=lambda c, v: setattr(c, 'condition9_high_price', v),
        get_profit_line=lambda c: c.condition9_profit_line,
        set_profit_line=lambda c, v: setattr(c, 'condition9_profit_line', v),
        get_sell_times=lambda c: c.condition9_sell_times,
        inc_sell_times=lambda c: setattr(c, 'condition9_sell_times', c.condition9_sell_times + 1),
    )