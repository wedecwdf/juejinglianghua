# domain/contexts/condition8.py
# -*- coding: utf-8 -*-
"""
条件8动态基准价网格交易上下文
移除对 config.strategy 的直接导入，配置通过构造函数注入。
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from .base import BaseConditionContext


class Condition8Context(BaseConditionContext):
    __slots__ = (
        'condition8_reference_price',
        'condition8_trade_times',
        'condition8_last_trade_price',
        'condition8_upper_band',
        'condition8_lower_band',
        'condition8_sleeping',
        'condition8_last_trigger_price',
        'condition8_last_trigger_time',
        'condition8_cooldown_period',
        'condition8_sell_triggered_for_current_ref',
        'condition8_buy_triggered_for_current_ref',
        'condition8_total_buy_today',
        'condition8_total_sell_today',
        'condition8_last_done_price',
        'condition8_has_done_trade',
    )

    def __init__(self, base_price: float,
                 upper_band_percent: float = 0.16,
                 lower_band_percent: float = 0.16):
        self.condition8_reference_price: float = base_price
        self.condition8_trade_times: int = 0
        self.condition8_last_trade_price: Optional[float] = None
        self.condition8_upper_band: Optional[float] = (
            base_price * (1 + upper_band_percent) if base_price else None
        )
        self.condition8_lower_band: Optional[float] = (
            base_price * (1 - lower_band_percent) if base_price else None
        )
        self.condition8_sleeping: bool = False
        self.condition8_last_trigger_price: Optional[float] = None
        self.condition8_last_trigger_time: Optional[float] = None
        self.condition8_cooldown_period: int = 5
        self.condition8_sell_triggered_for_current_ref: bool = False
        self.condition8_buy_triggered_for_current_ref: bool = False
        self.condition8_total_buy_today: int = 0
        self.condition8_total_sell_today: int = 0
        self.condition8_last_done_price: Optional[float] = None
        self.condition8_has_done_trade: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {slot: getattr(self, slot) for slot in self.__slots__}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Condition8Context':
        # 反序列化时用默认值，实际波段可能丢失，但通常从配置重新注入
        ctx = cls(data.get('condition8_reference_price', 0.0))
        for slot in cls.__slots__:
            if slot in data:
                setattr(ctx, slot, data[slot])
        return ctx