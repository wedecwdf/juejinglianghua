# -*- coding: utf-8 -*-
"""
次日固定止损机制状态
"""

from __future__ import annotations
from typing import Dict, Any
from .base import BaseState


class NextDayState(BaseState):
    __slots__ = ('dynamic_profit_next_day_adjustment',)

    def __init__(self) -> None:
        self.dynamic_profit_next_day_adjustment: Dict[str, Any] = {
            'enabled': False,
            'stop_loss_price': -float('inf'),
            'sell_ratio': 0.0,
            'days_count': 0,
            'condition2_high_line': -float('inf'),
            'condition9_high_line': -float('inf'),
            'condition2_activated': False,
            'condition9_activated': False,
        }