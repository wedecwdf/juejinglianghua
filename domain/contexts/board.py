# domain/contexts/board.py
# -*- coding: utf-8 -*-
"""板数/炸板/断板上下文（聚合 BoardStatus 等）"""
from __future__ import annotations
from typing import Dict, Any, Optional
from domain.board import BoardStatus, BoardBreakState
from .base import BaseConditionContext


class BoardStateContext(BaseConditionContext):
    __slots__ = (
        'board_status',
        'board_break_status',
        '_board_break_state',
    )

    def __init__(self):
        self.board_status: BoardStatus = BoardStatus()
        # 存储炸板状态，与 board_status._board_break_state 同步
        self._board_break_state: str = BoardBreakState.SEALED.value

    def sync(self):
        """确保内部字符串状态与 BoardStatus 一致，此处简化处理"""
        self._board_break_state = self.board_status.get_break_state().value

    def to_dict(self) -> Dict[str, Any]:
        # 不持久化 BoardStatus 对象，由 BoardStateRepository 管理
        raise NotImplementedError("BoardStateContext 不直接序列化，由仓库管理")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoardStateContext':
        raise NotImplementedError