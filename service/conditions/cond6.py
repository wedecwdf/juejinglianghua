# service/conditions/cond6.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.contexts.condition4_7 import Condition4To7Context
from config.strategy import CONDITION6_ENABLED, BUY_BELOW_MA12_QUANTITY

def check_condition6(day_data: DayData, context: Condition4To7Context,
                     current_price: float) -> Optional[Dict[str, Any]]:
    if (CONDITION6_ENABLED and day_data.ma12 is not None and
            current_price < day_data.ma12 and not context.buy_condition6_triggered):
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