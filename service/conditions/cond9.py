# -*- coding: utf-8 -*-
"""
条件9：第一区间动态止盈（重构版，调用公共内核）
"""
from __future__ import annotations
from typing import Optional, Dict, Any

from domain.day_data import DayData
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


def check_condition9(day_data: DayData, increase: float,
                     current_price: float, base_price: float,
                     board_break_active: bool = False,
                     condition2_active: bool = False) -> Optional[Dict[str, Any]]:
    """
    条件9第一区间动态止盈入口 - 委托给公共内核处理

    特殊处理：
    - 条件2优先级覆盖检查
    - 价格区间边界检查（超出区间停止监测）
    """
    # 条件9特有：检查是否被条件2触发互斥
    if day_data.condition2_triggered_and_sold:
        return None

    # 条件9特有：检查是否已停止监测
    if day_data.condition9_stopped:
        return None

    # 条件9特有：价格区间检查（超出区间则停止监测）
    upper_band = base_price * (1 + CONDITION9_UPPER_BAND_PERCENT)
    lower_band = base_price * (1 - CONDITION9_LOWER_BAND_PERCENT)

    if current_price > upper_band:
        day_data.condition9_stopped = True
        day_data.condition9_triggered = False
        print(f'【条件9停止监测】价格突破区间上限，停止监测')
        return None

    # 条件9特有：条件2优先级覆盖（清理状态）
    def _priority_check():
        if condition2_active:
            if day_data.condition9_triggered:
                day_data.condition9_triggered = False
                day_data.condition9_high_price = float('-inf')
                day_data.condition9_profit_line = float('-inf')
                print(f"【优先级覆盖】{day_data.symbol} 条件二激活，条件九状态被清理")
            return True
        return False

    # 检查是否在价格区间内
    if not (lower_band <= current_price <= upper_band):
        return None

    return _check_dynamic_profit_core(
        day_data=day_data,
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
        triggered_flag_attr='condition9_triggered',
        high_price_attr='condition9_high_price',
        profit_line_attr='condition9_profit_line',
        sell_times_attr='condition9_sell_times',
        condition_name='条件9',
        board_break_active=board_break_active,
        priority_check_fn=_priority_check
    )