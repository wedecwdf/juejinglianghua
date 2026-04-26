# domain/stores/base.py
# -*- coding: utf-8 -*-
"""存储抽象基类"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.board import BoardStatus, BoardCountData, BoardBreakStatus

class AbstractSessionRegistry(ABC):
    @abstractmethod
    def get(self, symbol: str) -> Optional[DayData]:
        ...

    @abstractmethod
    def set(self, symbol: str, day_data: DayData) -> None:
        ...

    @abstractmethod
    def all_symbols(self) -> list[str]:
        ...

    @abstractmethod
    def items(self) -> Dict[str, DayData]:
        ...

    @abstractmethod
    def get_total_buy_quantity(self, symbol: str) -> int:
        ...

    @abstractmethod
    def set_total_buy_quantity(self, symbol: str, quantity: int) -> None:
        ...

    @abstractmethod
    def reset_total_buy(self, symbol: str) -> None:
        ...

    @abstractmethod
    def save(self) -> None:
        ...

    @abstractmethod
    def load(self) -> None:
        ...

class AbstractOrderLedger(ABC):
    @abstractmethod
    def add_pending_order(self, cl_ord_id: str, data: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def remove_pending_order(self, cl_ord_id: str) -> None:
        ...

    @abstractmethod
    def get_pending_order(self, cl_ord_id: str) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def get_all_pending_orders(self) -> Dict[str, Dict[str, Any]]:
        ...

    @abstractmethod
    def add_condition_trigger(self, cl_ord_id: str, trigger_info: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def remove_condition_trigger(self, cl_ord_id: str) -> None:
        ...

    @abstractmethod
    def get_condition_trigger(self, cl_ord_id: str) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def cancel_condition8_opposite(self, symbol: str, keep_cl_ord_id: str) -> None:
        ...

    @abstractmethod
    def get_condition8_pending_pool(self, symbol: str) -> Dict[str, str]:
        ...

    @abstractmethod
    def record_condition8_done_price(self, symbol: str, done_price: float) -> None:
        ...

    @abstractmethod
    def clear_condition8_state(self, symbol: str) -> None:
        ...

    @abstractmethod
    def acquire_cancel_lock(self, symbol: str) -> bool:
        ...

    @abstractmethod
    def release_cancel_lock(self, symbol: str) -> None:
        ...

    @abstractmethod
    def mark_cancelled(self, symbol: str) -> None:
        ...

    @abstractmethod
    def pop_cancelled(self, symbol: str) -> bool:
        ...

    @abstractmethod
    def is_cancelling(self, symbol: str) -> bool:
        ...

    @abstractmethod
    def get_sleep_state(self) -> bool:
        ...

    @abstractmethod
    def set_sleep_state(self, state: bool) -> None:
        ...

    @abstractmethod
    def is_condition8_sleeping(self) -> bool:
        ...

    @abstractmethod
    def save(self) -> None:
        ...

    @abstractmethod
    def load(self) -> None:
        ...

class AbstractBoardStateRepository(ABC):
    @abstractmethod
    def get_board_status(self, symbol: str) -> BoardStatus:
        ...

    @abstractmethod
    def get_board_count_data(self, symbol: str) -> Optional[BoardCountData]:
        ...

    @abstractmethod
    def set_board_count_data(self, symbol: str, data: Optional[BoardCountData]) -> None:
        ...

    @abstractmethod
    def get_board_break_status(self, symbol: str) -> BoardBreakStatus:
        ...

    @abstractmethod
    def save(self) -> None:
        ...

    @abstractmethod
    def load(self) -> None:
        ...

class AbstractCallbackTaskStore(ABC):
    @abstractmethod
    def get_task(self, symbol: str) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def set_task(self, symbol: str, data: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def remove_task(self, symbol: str) -> None:
        ...

    @abstractmethod
    def all_tasks(self) -> Dict[str, Dict[str, Any]]:
        ...

    @abstractmethod
    def save(self) -> None:
        ...

    @abstractmethod
    def load(self) -> None:
        ...