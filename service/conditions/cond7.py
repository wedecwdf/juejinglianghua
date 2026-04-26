# service/conditions/cond7.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.contexts.condition4_7 import Condition4To7Context
from config.strategy import CONDITION7_ENABLED

def check_condition7(day_data: DayData, context: Condition4To7Context,
                     current_price: float, tick_time) -> Optional[Dict[str, Any]]:
    if (CONDITION7_ENABLED and tick_time.hour == 14 and tick_time.minute >= 54 and
            day_data.ma4 is not None and current_price < day_data.ma4 and
            not context.condition7_triggered):
        return {
            'reason': '14:54后低于MA4卖出',
            'sell_price_offset': 0.01,
            'trigger_data': {
                'pre_trigger_state': False,
                'pre_buy_quantity': 0
            }
        }
    return None