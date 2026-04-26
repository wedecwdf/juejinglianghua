# -*- coding: utf-8 -*-
"""
技术指标状态（MA、CCI）
"""

from __future__ import annotations
from typing import Optional
from .base import BaseState


class IndicatorState(BaseState):
    __slots__ = (
        'ma4', 'ma8', 'ma12',
        'cci', 'cci_warning_triggered',
    )

    def __init__(self) -> None:
        self.ma4: Optional[float] = None
        self.ma8: Optional[float] = None
        self.ma12: Optional[float] = None
        self.cci: Optional[float] = None
        self.cci_warning_triggered: bool = False