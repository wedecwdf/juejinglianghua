# -*- coding: utf-8 -*-
"""
条件2（动态止盈）状态
"""

from __future__ import annotations
from .base import BaseState


class Condition2State(BaseState):
    __slots__ = (
        'dynamic_profit_triggered', 'dynamic_profit_high_price',
        'dynamic_profit_line', 'dynamic_profit_sell_times',
        'condition2_triggered', 'condition2_triggered_and_sold',
    )

    def __init__(self) -> None:
        self.dynamic_profit_triggered: bool = False
        self.dynamic_profit_high_price: float = -float('inf')
        self.dynamic_profit_line: float = -float('inf')
        self.dynamic_profit_sell_times: int = 0
        self.condition2_triggered: bool = False
        self.condition2_triggered_and_sold: bool = False