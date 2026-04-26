# service/conditions/cond4.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.contexts.condition4_7 import Condition4To7Context
from config.strategy import CONDITION4_ENABLED, BUY_BELOW_MA4_QUANTITY

def check_condition4(day_data: DayData, context: Condition4To7Context,
                     current_price: float) -> Optional[Dict[str, Any]]:
    if (CONDITION4_ENABLED and day_data.ma4 is not None and
            current_price < day_data.ma4 and not context.buy_condition4_triggered):
        return {
            'reason': '低于MA4买入',
            'quantity': BUY_BELOW_MA4_QUANTITY,
            'trigger_data': {
                'quantity': BUY_BELOW_MA4_QUANTITY,
                'pre_trigger_state': False,
                'pre_buy_quantity': 0
            }
        }
    return None