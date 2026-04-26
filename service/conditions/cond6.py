# -*- coding: utf-8 -*-
"""
条件6：低于MA12买入
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.day_data import DayData
from config.strategy import CONDITION6_ENABLED, BUY_BELOW_MA12_QUANTITY


def check_condition6(day_data: DayData, current_price: float) -> Optional[Dict[str, Any]]:
    if (CONDITION6_ENABLED and day_data.ma12 is not None and
            current_price < day_data.ma12 and not day_data.buy_condition6_triggered):
        return {
            'reason': '低于MA12买入',
            'quantity': BUY_BELOW_MA12_QUANTITY,
            'trigger_data': {
                'quantity': BUY_BELOW_MA12_QUANTITY,
                'pre_trigger_state': False,
                'pre_buy_quantity': 0
            }
        }
    return None