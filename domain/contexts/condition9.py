# domain/contexts/condition9.py
# -*- coding: utf-8 -*-
"""
条件9第一区间动态止盈上下文
移除对 config.strategy 的直接导入，配置通过构造函数注入。
"""
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
        'recheck_after_cancel',
        'post_cancel_rechecked',
    )

    def __init__(self, base_price: float,
                 upper_band_percent: float = 0.02,
                 lower_band_percent: float = 0.001):
        self.condition9_triggered: bool = False
        self.condition9_high_price: float = -float('inf')
        self.condition9_profit_line: float = -float('inf')
        self.condition9_sell_times: int = 0
        self.condition9_upper_band: Optional[float] = (
            base_price * (1 + upper_band_percent) if base_price else None
        )
        self.condition9_lower_band: Optional[float] = (
            base_price * (1 - lower_band_percent) if base_price else None
        )
        self.condition9_stopped: bool = False
        self.condition9_triggered_for_spacing: bool = False
        self.recheck_after_cancel: bool = False
        self.post_cancel_rechecked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {slot: getattr(self, slot) for slot in self.__slots__}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Condition9Context':
        base_price = data.get('base_price', 0.0)  # 从持久化中无法获取区间，使用默认
        ctx = cls(base_price)
        for slot in cls.__slots__:
            if slot in data:
                setattr(ctx, slot, data[slot])
        return ctx