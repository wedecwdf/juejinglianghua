# repository/stores/order_ledger_impl.py
# -*- coding: utf-8 -*-
"""OrderLedger 具体实现，封装 StateGateway"""
from __future__ import annotations
from typing import Dict, Any, Optional
from domain.stores.base import AbstractOrderLedger

class OrderLedgerImpl(AbstractOrderLedger):
    def __init__(self, gateway=None):
        from repository.state_gateway import StateGateway
        self._gw = gateway if gateway is not None else StateGateway()

    def add_pending_order(self, cl_ord_id: str, data: Dict[str, Any]) -> None:
        self._gw.add_pending_order(cl_ord_id, data)

    def remove_pending_order(self, cl_ord_id: str) -> None:
        self._gw.remove_pending_order(cl_ord_id)

    def get_pending_order(self, cl_ord_id: str) -> Optional[Dict[str, Any]]:
        return self._gw.get_pending_order(cl_ord_id)

    def get_all_pending_orders(self) -> Dict[str, Dict[str, Any]]:
        return self._gw.pending_orders

    def add_condition_trigger(self, cl_ord_id: str, trigger_info: Dict[str, Any]) -> None:
        self._gw.add_pending_condition_trigger(cl_ord_id, trigger_info)

    def remove_condition_trigger(self, cl_ord_id: str) -> None:
        self._gw.remove_pending_condition_trigger(cl_ord_id)

    def get_condition_trigger(self, cl_ord_id: str) -> Optional[Dict[str, Any]]:
        return self._gw.get_pending_condition_trigger(cl_ord_id)

    def cancel_condition8_opposite(self, symbol: str, keep_cl_ord_id: str) -> None:
        self._gw.cancel_condition8_opposite(symbol, keep_cl_ord_id)

    def get_condition8_pending_pool(self, symbol: str) -> Dict[str, str]:
        return self._gw.condition8_pending.get(symbol, {})

    def record_condition8_done_price(self, symbol: str, done_price: float) -> None:
        self._gw.record_condition8_done_price(symbol, done_price)

    def clear_condition8_state(self, symbol: str) -> None:
        self._gw.clear_condition8_state(symbol)

    def acquire_cancel_lock(self, symbol: str) -> bool:
        return self._gw.acquire_cancel_lock(symbol)

    def release_cancel_lock(self, symbol: str) -> None:
        self._gw.release_cancel_lock(symbol)

    def mark_cancelled(self, symbol: str) -> None:
        self._gw.mark_cancelled(symbol)

    def pop_cancelled(self, symbol: str) -> bool:
        return self._gw.pop_cancelled(symbol)

    def is_cancelling(self, symbol: str) -> bool:
        return self._gw.is_cancelling(symbol)

    def get_sleep_state(self) -> bool:
        return self._gw.get_sleep_state()

    def set_sleep_state(self, state: bool) -> None:
        self._gw.set_sleep_state(state)

    def is_condition8_sleeping(self) -> bool:
        return self._gw.is_condition8_sleeping()

    def save(self) -> None:
        self._gw._save_pending_orders()
        self._gw._save_condition_triggers()

    def load(self) -> None:
        self._gw._load_pending_orders()
        self._gw._load_condition_triggers()