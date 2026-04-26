# -*- coding: utf-8 -*-
"""
条件2：动态止盈（重构版，调用公共内核）
"""
from __future__ import annotations
from typing import Optional, Dict, Any

from domain.day_data import DayData
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


def check_condition2(day_data: DayData, increase: float,
                     current_price: float, base_price: float,
                     board_break_active: bool = False) -> Optional[Dict[str, Any]]:
    """
    条件2动态止盈入口 - 委托给公共内核处理
    """
    return _check_dynamic_profit_core(
        day_data=day_data,
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
        triggered_flag_attr='dynamic_profit_triggered',
        high_price_attr='dynamic_profit_high_price',
        profit_line_attr='dynamic_profit_line',
        sell_times_attr='dynamic_profit_sell_times',
        condition_name='条件2',
        board_break_active=board_break_active
    )