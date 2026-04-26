# repository/stores/session_registry_impl.py
# -*- coding: utf-8 -*-
"""SessionRegistry 具体实现，封装 StateGateway"""
from __future__ import annotations
from typing import Optional, Dict
from domain.day_data import DayData
from domain.stores.base import AbstractSessionRegistry

class SessionRegistryImpl(AbstractSessionRegistry):
    def __init__(self, gateway=None):
        from repository.state_gateway import StateGateway
        self._gw = gateway if gateway is not None else StateGateway()

    def get(self, symbol: str) -> Optional[DayData]:
        return self._gw.current_day_data.get(symbol)

    def set(self, symbol: str, day_data: DayData) -> None:
        self._gw.current_day_data[symbol] = day_data

    def all_symbols(self) -> list[str]:
        return list(self._gw.current_day_data.keys())

    def items(self) -> Dict[str, DayData]:
        return self._gw.current_day_data

    def get_total_buy_quantity(self, symbol: str) -> int:
        return self._gw.total_buy_quantity.get(symbol, 0)

    def set_total_buy_quantity(self, symbol: str, quantity: int) -> None:
        self._gw.total_buy_quantity[symbol] = quantity

    def reset_total_buy(self, symbol: str) -> None:
        self._gw.total_buy_quantity[symbol] = 0

    def save(self) -> None:
        self._gw._save_strategy_state()

    def load(self) -> None:
        self._gw._load_strategy_state()