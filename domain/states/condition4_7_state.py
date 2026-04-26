# -*- coding: utf-8 -*-
"""
条件4-7（MA均线交易）状态
"""

from __future__ import annotations
from .base import BaseState


class Condition4To7State(BaseState):
    __slots__ = (
        'buy_condition4_triggered', 'buy_condition5_triggered',
        'buy_condition6_triggered', 'condition7_triggered',
    )

    def __init__(self) -> None:
        self.buy_condition4_triggered: bool = False
        self.buy_condition5_triggered: bool = False
        self.buy_condition6_triggered: bool = False
        self.condition7_triggered: bool = False