# domain/contexts/pyramid.py
# -*- coding: utf-8 -*-
"""金字塔止盈上下文"""
from __future__ import annotations
from typing import Dict, Any, List
from .base import BaseConditionContext


class PyramidContext(BaseConditionContext):
    __slots__ = (
        'pyramid_profit_triggered',
        'pyramid_profit_status',
        'pyramid_profit_base_price',
    )

    def __init__(self, base_price: float):
        self.pyramid_profit_triggered: bool = False
        self.pyramid_profit_status: List[bool] = [False, False, False]
        self.pyramid_profit_base_price: float = base_price

    def to_dict(self) -> Dict[str, Any]:
        return {slot: getattr(self, slot) for slot in self.__slots__}

    @classmethod
    def from_dict(cls, base_price: float, data: Dict[str, Any]) -> 'PyramidContext':
        ctx = cls(base_price)
        for slot in cls.__slots__:
            if slot in data:
                setattr(ctx, slot, data[slot])
        return ctx