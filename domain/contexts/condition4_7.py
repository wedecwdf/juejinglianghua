# domain/contexts/condition4_7.py
# -*- coding: utf-8 -*-
"""条件4-7（MA交易）上下文"""
from __future__ import annotations
from typing import Dict, Any
from .base import BaseConditionContext


class Condition4To7Context(BaseConditionContext):
    __slots__ = (
        'buy_condition4_triggered',
        'buy_condition5_triggered',
        'buy_condition6_triggered',
        'condition7_triggered',
    )

    def __init__(self):
        self.buy_condition4_triggered: bool = False
        self.buy_condition5_triggered: bool = False
        self.buy_condition6_triggered: bool = False
        self.condition7_triggered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {slot: getattr(self, slot) for slot in self.__slots__}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Condition4To7Context':
        ctx = cls()
        for slot in cls.__slots__:
            if slot in data:
                setattr(ctx, slot, data[slot])
        return ctx