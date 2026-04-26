# service/conditions/cond2.py
# -*- coding: utf-8 -*-
"""
条件2：动态止盈（直接操作 Condition2Context）
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.contexts.condition2 import Condition2Context
from config.strategy import (
    CONDITION2_ENABLED,
    CONDITION2_DYNAMIC_PROFIT_ENABLED,
    MAX_DYNAMIC_PROFIT_SELL_TIMES,
    CONDITION2_TRIGGER_PERCENT,
    CONDITION2_DECLINE_PERCENT,
    CONDITION2_SELL_PRICE_OFFSET,
    CONDITION2_DYNAMIC_LINE_THRESHOLD,
    CONDITION2_SELL_PERCENT_HIGH,
    CONDITION2_SELL_PERCENT_LOW,
)
from .utils import _check_dynamic_profit_core

def check_condition2(
    context: Condition2Context,
    increase: float,
    current_price: float,
    base_price: float,
    board_break_active: bool = False
) -> Optional[Dict[str, Any]]:
    return _check_dynamic_profit_core(
        context=context,
        increase=increase,
        current_price=current_price,
        base_price=base_price,
        enabled=CONDITION2_ENABLED and CONDITION2_DYNAMIC_PROFIT_ENABLED,
        max_sell_times=MAX_DYNAMIC_PROFIT_SELL_TIMES,
        trigger_percent=CONDITION2_TRIGGER_PERCENT,
        decline_percent=CONDITION2_DECLINE_PERCENT,
        sell_price_offset=CONDITION2_SELL_PRICE_OFFSET,
        dynamic_line_threshold=CONDITION2_DYNAMIC_LINE_THRESHOLD,
        sell_percent_high=CONDITION2_SELL_PERCENT_HIGH,
        sell_percent_low=CONDITION2_SELL_PERCENT_LOW,
        condition_name='条件2',
        board_break_active=board_break_active,
        get_triggered=lambda c: c.dynamic_profit_triggered,
        set_triggered=lambda c, v: setattr(c, 'dynamic_profit_triggered', v),
        get_high_price=lambda c: c.dynamic_profit_high_price,
        set_high_price=lambda c, v: setattr(c, 'dynamic_profit_high_price', v),
        get_profit_line=lambda c: c.dynamic_profit_line,
        set_profit_line=lambda c, v: setattr(c, 'dynamic_profit_line', v),
        get_sell_times=lambda c: c.dynamic_profit_sell_times,
        inc_sell_times=lambda c: setattr(c, 'dynamic_profit_sell_times', c.dynamic_profit_sell_times + 1),
    )