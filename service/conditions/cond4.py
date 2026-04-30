# service/conditions/cond4.py
# -*- coding: utf-8 -*-
"""
条件4：低于MA4买入，通过 config 参数获取开关和数量。
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.contexts.condition4_7 import Condition4To7Context
from config.strategy.config_objects import MaTradingConfig


def check_condition4(day_data: DayData, context: Condition4To7Context,
                     current_price: float,
                     config: MaTradingConfig) -> Optional[Dict[str, Any]]:
    if (config.condition4_enabled and day_data.ma4 is not None and
            current_price < day_data.ma4 and not context.buy_condition4_triggered):
        return {
            'reason': '低于MA4买入',
            'quantity': config.buy_below_ma4_qty,
            'trigger_data': {
                'quantity': config.buy_below_ma4_qty,
                'pre_trigger_state': False,
                'pre_buy_quantity': 0
            }
        }
    return None