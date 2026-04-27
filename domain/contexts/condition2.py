# domain/contexts/condition2.py
# -*- coding: utf-8 -*-
"""
条件2动态止盈运行时上下文
"""
from __future__ import annotations
from typing import Dict, Any
from .base import BaseConditionContext


class Condition2Context(BaseConditionContext):
    __slots__ = (
        'dynamic_profit_triggered',
        'dynamic_profit_high_price',
        'dynamic_profit_line',
        'dynamic_profit_sell_times',
        'condition2_triggered_and_sold',
        'recheck_after_cancel',
        'post_cancel_rechecked',
    )

    def __init__(self):
        self.dynamic_profit_triggered: bool = False
        self.dynamic_profit_high_price: float = -float('inf')
        self.dynamic_profit_line: float = -float('inf')
        self.dynamic_profit_sell_times: int = 0
        self.condition2_triggered_and_sold: bool = False
        self.recheck_after_cancel: bool = False
        self.post_cancel_rechecked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {slot: getattr(self, slot) for slot in self.__slots__}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Condition2Context':
        ctx = cls()
        for slot in cls.__slots__:
            if slot in data:
                setattr(ctx, slot, data[slot])
        return ctx