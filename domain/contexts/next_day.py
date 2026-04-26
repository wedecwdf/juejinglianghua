# domain/contexts/next_day.py
# -*- coding: utf-8 -*-
"""次日固定止损机制上下文"""
from __future__ import annotations
from typing import Dict, Any
from .base import BaseConditionContext


class NextDayAdjustmentContext(BaseConditionContext):
    __slots__ = ('data',)

    def __init__(self):
        self.data: Dict[str, Any] = {
            'enabled': False,
            'stop_loss_price': -float('inf'),
            'sell_ratio': 0.0,
            'days_count': 0,
            'condition2_high_line': -float('inf'),
            'condition9_high_line': -float('inf'),
            'condition2_activated': False,
            'condition9_activated': False,
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.data.copy()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NextDayAdjustmentContext':
        ctx = cls()
        ctx.data = data.copy()
        return ctx