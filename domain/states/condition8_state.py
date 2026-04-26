# -*- coding: utf-8 -*-
"""
条件8（动态基准价网格交易）状态
"""

from __future__ import annotations
from typing import Optional
from .base import BaseState


class Condition8State(BaseState):
    __slots__ = (
        'condition8_reference_price', 'condition8_trade_times',
        'condition8_last_trade_price', 'condition8_upper_band',
        'condition8_lower_band', 'condition8_sleeping',
        'condition8_last_trigger_price', 'condition8_last_trigger_time',
        'condition8_cooldown_period', 'condition8_sell_triggered_for_current_ref',
        'condition8_buy_triggered_for_current_ref', 'condition8_total_buy_today',
        'condition8_total_sell_today', 'condition8_last_done_price',
        'condition8_has_done_trade',
    )

    def __init__(self, base_price: float) -> None:
        self.condition8_reference_price: float = base_price
        self.condition8_trade_times: int = 0
        self.condition8_last_trade_price: Optional[float] = None

        from config.strategy import (
            CONDITION8_UPPER_BAND_PERCENT,
            CONDITION8_LOWER_BAND_PERCENT,
        )
        self.condition8_upper_band: Optional[float] = (
            base_price * (1 + CONDITION8_UPPER_BAND_PERCENT) if base_price else None
        )
        self.condition8_lower_band: Optional[float] = (
            base_price * (1 - CONDITION8_LOWER_BAND_PERCENT) if base_price else None
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