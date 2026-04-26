# repository/stores/callback_task_store_impl.py
# -*- coding: utf-8 -*-
"""CallbackTaskStore 具体实现，封装 StateGateway"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.stores.base import AbstractCallbackTaskStore

class CallbackTaskStoreImpl(AbstractCallbackTaskStore):
    def __init__(self, gateway=None):
        from repository.state_gateway import StateGateway
        self._gw = gateway if gateway is not None else StateGateway()

    def get_task(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self._gw.callback_addition_tasks.get(symbol)

    def set_task(self, symbol: str, data: Dict[str, Any]) -> None:
        self._gw.callback_addition_tasks[symbol] = data

    def remove_task(self, symbol: str) -> None:
        self._gw.callback_addition_tasks.pop(symbol, None)

    def all_tasks(self) -> Dict[str, Dict[str, Any]]:
        return self._gw.callback_addition_tasks

    def save(self) -> None:
        self._gw._save_callback_addition_tasks()

    def load(self) -> None:
        self._gw._load_callback_addition_tasks()