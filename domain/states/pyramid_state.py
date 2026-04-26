# -*- coding: utf-8 -*-
"""
金字塔止盈状态（已从条件8完全独立）
"""

from __future__ import annotations
from typing import List
from .base import BaseState


class PyramidState(BaseState):
    __slots__ = (
        'pyramid_profit_triggered', 'pyramid_profit_status',
        'pyramid_profit_base_price',
    )

    def __init__(self, base_price: float) -> None:
        self.pyramid_profit_triggered: bool = False
        self.pyramid_profit_status: List[bool] = [False, False, False]
        self.pyramid_profit_base_price: float = base_price