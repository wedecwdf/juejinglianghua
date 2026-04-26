# repository/stores/board_state_repo_impl.py
# -*- coding: utf-8 -*-
"""BoardStateRepository 具体实现，封装 StateGateway"""
from __future__ import annotations
from typing import Optional
from domain.board import BoardStatus, BoardCountData, BoardBreakStatus
from domain.stores.base import AbstractBoardStateRepository

class BoardStateRepositoryImpl(AbstractBoardStateRepository):
    def __init__(self, gateway=None):
        from repository.state_gateway import StateGateway
        self._gw = gateway if gateway is not None else StateGateway()

    def get_board_status(self, symbol: str) -> BoardStatus:
        return self._gw.get_board_status(symbol)

    def get_board_count_data(self, symbol: str) -> Optional[BoardCountData]:
        return self._gw.get_board_count_data(symbol)

    def set_board_count_data(self, symbol: str, data: Optional[BoardCountData]) -> None:
        self._gw.set_board_count_data(symbol, data)

    def get_board_break_status(self, symbol: str) -> BoardBreakStatus:
        return self._gw.get_board_break_status(symbol)

    def save(self) -> None:
        self._gw._save_board_count()

    def load(self) -> None:
        self._gw._load_board_count()