# service/conditions/cond5.py
# -*- coding: utf-8 -*-
"""
条件5：低于MA8买入，通过 config 参数获取开关和数量。
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.contexts.condition4_7 import Condition4To7Context
from config.strategy.config_objects import MaTradingConfig


def check_condition5(day_data: DayData, context: Condition4To7Context,
                     current_price: float,
                     config: MaTradingConfig) -> Optional[Dict[str, Any]]:
    if (config.condition5_enabled and day_data.ma8 is not None and
            current_price < day_data.ma8 and not context.buy_condition5_triggered):
        return {
            'reason': '低于MA8买入',
            'quantity': config.buy_below_ma8_qty,
            'trigger_data': {
                'quantity': config.buy_below_ma8_qty,
                'pre_trigger_state': False,
                'pre_buy_quantity': 0
            }
        }
    return None