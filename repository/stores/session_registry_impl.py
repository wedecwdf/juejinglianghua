# repository/stores/session_registry_impl.py
# -*- coding: utf-8 -*-
"""
SessionRegistry 具体实现，脱离 StateGateway，直接管理内存字典和持久化。
并负责条件上下文的创建与获取。
"""
from __future__ import annotations
from typing import Optional, Dict
from domain.day_data import DayData
from domain.stores.base import AbstractSessionRegistry
from domain.contexts import (
    Condition2Context,
    Condition8Context,
    Condition9Context,
    Condition4To7Context,
    BoardStateContext,
    PyramidContext,
    NextDayAdjustmentContext,
)
from repository.persistence.file_persistence import FilePersistence
from repository.core.file_path import STATE_FILE


class SessionRegistryImpl(AbstractSessionRegistry):
    def __init__(self):
        self._current_day_data: Dict[str, DayData] = {}
        self._total_buy_quantity: Dict[str, int] = {}
        self._total_sell_times: Dict[str, int] = {}

        # 条件上下文容器
        self._condition2: Dict[str, Condition2Context] = {}
        self._condition8: Dict[str, Condition8Context] = {}
        self._condition9: Dict[str, Condition9Context] = {}
        self._condition4_7: Dict[str, Condition4To7Context] = {}
        self._board: Dict[str, BoardStateContext] = {}
        self._pyramid: Dict[str, PyramidContext] = {}
        self._next_day: Dict[str, NextDayAdjustmentContext] = {}

        self._persistence = FilePersistence()

    # ---------- DayData ----------
    def get(self, symbol: str) -> Optional[DayData]:
        return self._current_day_data.get(symbol)

    def set(self, symbol: str, day_data: DayData) -> None:
        self._current_day_data[symbol] = day_data

    def all_symbols(self) -> list[str]:
        return list(self._current_day_data.keys())

    def items(self) -> Dict[str, DayData]:
        return self._current_day_data

    # ---------- 累计买入 ----------
    def get_total_buy_quantity(self, symbol: str) -> int:
        return self._total_buy_quantity.get(symbol, 0)

    def set_total_buy_quantity(self, symbol: str, quantity: int) -> None:
        self._total_buy_quantity[symbol] = quantity

    def reset_total_buy(self, symbol: str) -> None:
        self._total_buy_quantity[symbol] = 0

    # ---------- 总卖出次数 ----------
    def get_total_sell_times(self, symbol: str) -> int:
        return self._total_sell_times.get(symbol, 0)

    def increment_total_sell_times(self, symbol: str, delta: int = 1):
        self._total_sell_times[symbol] = self._total_sell_times.get(symbol, 0) + delta

    def reset_total_sell_times(self, symbol: str):
        self._total_sell_times[symbol] = 0

    # ---------- 条件上下文访问 ----------
    def get_condition2(self, symbol: str) -> Condition2Context:
        if symbol not in self._condition2:
            self._condition2[symbol] = Condition2Context()
        return self._condition2[symbol]

    def get_condition8(self, symbol: str, base_price: float) -> Condition8Context:
        if symbol not in self._condition8:
            self._condition8[symbol] = Condition8Context(base_price)
        return self._condition8[symbol]

    def get_condition9(self, symbol: str, base_price: float) -> Condition9Context:
        if symbol not in self._condition9:
            self._condition9[symbol] = Condition9Context(base_price)
        return self._condition9[symbol]

    def get_condition4_7(self, symbol: str) -> Condition4To7Context:
        if symbol not in self._condition4_7:
            self._condition4_7[symbol] = Condition4To7Context()
        return self._condition4_7[symbol]

    def get_board_context(self, symbol: str) -> BoardStateContext:
        if symbol not in self._board:
            self._board[symbol] = BoardStateContext()
        return self._board[symbol]

    def get_pyramid(self, symbol: str, base_price: float) -> PyramidContext:
        if symbol not in self._pyramid:
            self._pyramid[symbol] = PyramidContext(base_price)
        return self._pyramid[symbol]

    def get_next_day(self, symbol: str) -> NextDayAdjustmentContext:
        if symbol not in self._next_day:
            self._next_day[symbol] = NextDayAdjustmentContext()
        return self._next_day[symbol]

    # ---------- 持久化 ----------
    def save(self) -> None:
        state = {
            "current_day_data": {},
            "total_buy_quantity": self._total_buy_quantity.copy(),
            "total_sell_times": self._total_sell_times.copy(),
        }
        for sym, dd in self._current_day_data.items():
            state["current_day_data"][sym] = dd.to_dict()
        self._persistence.save(STATE_FILE, state)

    def load(self) -> None:
        state = self._persistence.load(STATE_FILE)
        if not state:
            return
        raw = state.get("current_day_data", {})
        for sym, dat in raw.items():
            self._current_day_data[sym] = DayData.from_dict(sym, dat)
        self._total_buy_quantity = state.get("total_buy_quantity", {})
        self._total_sell_times = state.get("total_sell_times", {})