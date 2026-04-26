# domain/contexts/condition9.py
# -*- coding: utf-8 -*-
"""条件9第一区间动态止盈上下文"""
from __future__ import annotations
from typing import Dict, Any, Optional
from .base import BaseConditionContext


class Condition9Context(BaseConditionContext):
    __slots__ = (
        'condition9_triggered',
        'condition9_high_price',
        'condition9_profit_line',
        'condition9_sell_times',
        'condition9_upper_band',
        'condition9_lower_band',
        'condition9_stopped',
        'condition9_triggered_for_spacing',
    )

    def __init__(self, base_price: float):
        self.condition9_triggered: bool = False
        self.condition9_high_price: float = -float('inf')
        self.condition9_profit_line: float = -float('inf')
        self.condition9_sell_times: int = 0
        from config.strategy import CONDITION9_UPPER_BAND_PERCENT, CONDITION9_LOWER_BAND_PERCENT
        self.condition9_upper_band: Optional[float] = (
            base_price * (1 + CONDITION9_UPPER_BAND_PERCENT) if base_price else None
        )
        self.condition9_lower_band: Optional[float] = (
            base_price * (1 - CONDITION9_LOWER_BAND_PERCENT) if base_price else None
        )
        self.condition9_stopped: bool = False
        self.condition9_triggered_for_spacing: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {slot: getattr(self, slot) for slot in self.__slots__}

    @classmethod
    def from_dict(cls, base_price: float, data: Dict[str, Any]) -> 'Condition9Context':
        ctx = cls(base_price)
        for slot in cls.__slots__:
            if slot in data:
                setattr(ctx, slot, data[slot])
        return ctx