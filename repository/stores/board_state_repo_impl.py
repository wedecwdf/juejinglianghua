# repository/stores/board_state_repo_impl.py
# -*- coding: utf-8 -*-
"""
板数、炸板、断板状态仓库实现，脱离 StateGateway。
"""
from __future__ import annotations
from typing import Optional
from domain.board import BoardStatus, BoardCountData, BoardBreakStatus
from domain.stores.base import AbstractBoardStateRepository
from repository.persistence.file_persistence import FilePersistence
from repository.core.file_path import BOARD_COUNT_FILE


class BoardStateRepositoryImpl(AbstractBoardStateRepository):
    def __init__(self):
        self._board_status: dict[str, BoardStatus] = {}
        self._board_break_status: dict[str, BoardBreakStatus] = {}
        self._board_count_data: dict[str, BoardCountData] = {}
        self._persistence = FilePersistence()

    def get_board_status(self, symbol: str) -> BoardStatus:
        if symbol not in self._board_status:
            self._board_status[symbol] = BoardStatus()
        return self._board_status[symbol]

    def get_board_count_data(self, symbol: str) -> Optional[BoardCountData]:
        return self._board_count_data.get(symbol)

    def set_board_count_data(self, symbol: str, data: Optional[BoardCountData]) -> None:
        if data is None:
            self._board_count_data.pop(symbol, None)
        else:
            self._board_count_data[symbol] = data

    def get_board_break_status(self, symbol: str) -> BoardBreakStatus:
        if symbol not in self._board_break_status:
            self._board_break_status[symbol] = BoardBreakStatus()
        return self._board_break_status[symbol]

    def save(self) -> None:
        data_to_save = {}
        for sym, obj in self._board_count_data.items():
            data_to_save[sym] = {slot: getattr(obj, slot) for slot in obj.__slots__}
        self._persistence.save(BOARD_COUNT_FILE, {"board_count_data": data_to_save})

    def load(self) -> None:
        raw = self._persistence.load(BOARD_COUNT_FILE)
        if not raw:
            return
        for sym, d in raw.get("board_count_data", {}).items():
            bcd = BoardCountData()
            for slot in bcd.__slots__:
                if slot in d:
                    setattr(bcd, slot, d[slot])
            self._board_count_data[sym] = bcd