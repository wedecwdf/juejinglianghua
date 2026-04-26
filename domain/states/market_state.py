# -*- coding: utf-8 -*-
"""
基础行情状态（开盘、最高、最低、收盘、成交量等）
"""

from __future__ import annotations
from typing import Optional
from datetime import date
from .base import BaseState


class MarketState(BaseState):
    __slots__ = (
        'open', 'high', 'low', 'close', 'volume',
        'initialized', 'base_price',
    )

    def __init__(self, base_price: float, current_date: date) -> None:
        self.open: Optional[float] = None
        self.high: float = -float('inf')
        self.low: float = float('inf')
        self.close: Optional[float] = None
        self.volume: int = 0
        self.initialized: bool = False
        self.base_price: float = base_price