# repository/stores/session_registry_impl.py
from __future__ import annotations
from typing import Optional, Dict
from domain.day_data import DayData
from domain.stores.base import AbstractSessionRegistry
from repository.persistence.file_persistence import FilePersistence
from repository.core.file_path import STATE_FILE

class SessionRegistryImpl(AbstractSessionRegistry):
    def __init__(self):
        self._current_day_data: Dict[str, DayData] = {}
        self._total_buy_quantity: Dict[str, int] = {}
        self._total_sell_times: Dict[str, int] = {}
        self._persistence = FilePersistence()

    def get(self, symbol: str) -> Optional[DayData]:
        return self._current_day_data.get(symbol)

    def set(self, symbol: str, day_data: DayData) -> None:
        self._current_day_data[symbol] = day_data

    def all_symbols(self) -> list[str]:
        return list(self._current_day_data.keys())

    def items(self) -> Dict[str, DayData]:
        return self._current_day_data

    def get_total_buy_quantity(self, symbol: str) -> int:
        return self._total_buy_quantity.get(symbol, 0)

    def set_total_buy_quantity(self, symbol: str, quantity: int) -> None:
        self._total_buy_quantity[symbol] = quantity

    def reset_total_buy(self, symbol: str) -> None:
        self._total_buy_quantity[symbol] = 0

    def get_total_sell_times(self, symbol: str) -> int:
        return self._total_sell_times.get(symbol, 0)

    def increment_total_sell_times(self, symbol: str, delta: int = 1):
        self._total_sell_times[symbol] = self._total_sell_times.get(symbol, 0) + delta

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