# -*- coding: utf-8 -*-
"""
杂项状态（通用计数器、循环交互字段、内部标志）
"""

from __future__ import annotations
from typing import Optional
from .base import BaseState


class MiscState(BaseState):
    __slots__ = (
        'rise_triggered', 'total_sell_times',
        'pyramid_activation_after_condition8', 'last_condition8_profit_price',
        'condition8_cycle_count', 'max_condition8_cycles',
        '_condition9_stopped_reset_today',
    )

    def __init__(self) -> None:
        self.rise_triggered: int = 0
        self.total_sell_times: int = 0
        self.pyramid_activation_after_condition8: bool = False
        self.last_condition8_profit_price: Optional[float] = None
        self.condition8_cycle_count: int = 0
        self.max_condition8_cycles: int = 3
        self._condition9_stopped_reset_today: bool = False