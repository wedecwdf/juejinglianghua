# domain/stores/session_registry.py
# -*- coding: utf-8 -*-
"""
交易日行情会话注册表，管理 DayData 和各个条件上下文。
补充公共接口，消除对外部 _gw 的穿透访问。
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.contexts import (
    Condition2Context,
    Condition8Context,
    Condition9Context,
    Condition4To7Context,
    BoardStateContext,
    PyramidContext,
    NextDayAdjustmentContext,
)

class SessionRegistry:
    def __init__(self, gateway=None):
        from repository.state_gateway import StateGateway
        self._gw = gateway if gateway is not None else StateGateway()
        # 条件上下文按 symbol 存储
        self._condition2: Dict[str, Condition2Context] = {}
        self._condition8: Dict[str, Condition8Context] = {}
        self._condition9: Dict[str, Condition9Context] = {}
        self._condition4_7: Dict[str, Condition4To7Context] = {}
        self._board: Dict[str, BoardStateContext] = {}
        self._pyramid: Dict[str, PyramidContext] = {}
        self._next_day: Dict[str, NextDayAdjustmentContext] = {}

    # ---------- DayData ----------
    def get(self, symbol: str) -> Optional[DayData]:
        return self._gw.current_day_data.get(symbol)

    def set(self, symbol: str, day_data: DayData) -> None:
        self._gw.current_day_data[symbol] = day_data

    def all_symbols(self) -> list[str]:
        return list(self._gw.current_day_data.keys())

    def items(self) -> Dict[str, DayData]:
        return self._gw.current_day_data

    # ---------- 累计买入量 ----------
    def get_total_buy_quantity(self, symbol: str) -> int:
        return self._gw.total_buy_quantity.get(symbol, 0)

    def set_total_buy_quantity(self, symbol: str, quantity: int) -> None:
        self._gw.total_buy_quantity[symbol] = quantity

    def reset_total_buy(self, symbol: str) -> None:
        self._gw.total_buy_quantity[symbol] = 0

    # ---------- 总卖出次数（原 _gw.total_sell_times） ----------
    def get_total_sell_times(self, symbol: str) -> int:
        return self._gw.total_sell_times.get(symbol, 0)

    def increment_total_sell_times(self, symbol: str, delta: int = 1):
        self._gw.total_sell_times[symbol] = self._gw.total_sell_times.get(symbol, 0) + delta

    def reset_total_sell_times(self, symbol: str):
        self._gw.total_sell_times[symbol] = 0

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
        self._gw._save_strategy_state()

    def load(self) -> None:
        self._gw._load_strategy_state()