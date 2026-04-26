# -*- coding: utf-8 -*-
"""
动态止盈撤单后重新判定状态
"""

from __future__ import annotations
from .base import BaseState


class RecheckState(BaseState):
    __slots__ = (
        'condition2_recheck_after_cancel', 'condition9_recheck_after_cancel',
        'condition2_post_cancel_rechecked', 'condition9_post_cancel_rechecked',
    )

    def __init__(self) -> None:
        self.condition2_recheck_after_cancel: bool = False
        self.condition9_recheck_after_cancel: bool = False
        self.condition2_post_cancel_rechecked: bool = False
        self.condition9_post_cancel_rechecked: bool = False