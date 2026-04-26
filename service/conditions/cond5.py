# -*- coding: utf-8 -*-
"""
条件5：低于MA8买入
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.day_data import DayData
from config.strategy import CONDITION5_ENABLED, BUY_BELOW_MA8_QUANTITY


def check_condition5(day_data: DayData, current_price: float) -> Optional[Dict[str, Any]]:
    if (CONDITION5_ENABLED and day_data.ma8 is not None and
            current_price < day_data.ma8 and not day_data.buy_condition5_triggered):
        return {
            'reason': '低于MA8买入',
            'quantity': BUY_BELOW_MA8_QUANTITY,
            'trigger_data': {
                'quantity': BUY_BELOW_MA8_QUANTITY,
                'pre_trigger_state': False,
                'pre_buy_quantity': 0
            }
        }
    return None