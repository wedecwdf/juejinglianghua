# domain/stores/base.py
# -*- coding: utf-8 -*-
"""
领域存储库抽象接口。抽象 SessionRegistry 只管理行情和买入量计数，
不包含条件相关方法。AbstractOrderLedger 已拆分为多个小接口。
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.board import BoardStatus, BoardCountData, BoardBreakStatus
from .order_interfaces import (
    OrderRepository,
    ConditionTriggerRepo,
    CancelLockManager,
    SleepStateManager,
    Condition8OrderTracker,
)


class AbstractSessionRegistry(ABC):
    @abstractmethod
    def get(self, symbol: str) -> Optional[DayData]: ...
    @abstractmethod
    def set(self, symbol: str, day_data: DayData) -> None: ...
    @abstractmethod
    def all_symbols(self) -> list[str]: ...
    @abstractmethod
    def items(self) -> Dict[str, DayData]: ...
    @abstractmethod
    def get_total_buy_quantity(self, symbol: str) -> int: ...
    @abstractmethod
    def set_total_buy_quantity(self, symbol: str, quantity: int) -> None: ...
    @abstractmethod
    def reset_total_buy(self, symbol: str) -> None: ...
    @abstractmethod
    def get_total_sell_times(self, symbol: str) -> int: ...
    @abstractmethod
    def increment_total_sell_times(self, symbol: str, delta: int = 1): ...
    @abstractmethod
    def save(self) -> None: ...
    @abstractmethod
    def load(self) -> None: ...


class AbstractOrderLedger(
    OrderRepository,
    ConditionTriggerRepo,
    CancelLockManager,
    SleepStateManager,
    Condition8OrderTracker,
    ABC,
):
    """组合接口，向后兼容原有调用。"""
    # 所有方法均在上述基类中定义，此组合类无需重复声明
    ...


class AbstractBoardStateRepository(ABC):
    @abstractmethod
    def get_board_status(self, symbol: str) -> BoardStatus: ...
    @abstractmethod
    def get_board_count_data(self, symbol: str) -> Optional[BoardCountData]: ...
    @abstractmethod
    def set_board_count_data(self, symbol: str, data: Optional[BoardCountData]) -> None: ...
    @abstractmethod
    def get_board_break_status(self, symbol: str) -> BoardBreakStatus: ...
    @abstractmethod
    def save(self) -> None: ...
    @abstractmethod
    def load(self) -> None: ...


class AbstractCallbackTaskStore(ABC):
    @abstractmethod
    def get_task(self, symbol: str) -> Optional[Dict[str, Any]]: ...
    @abstractmethod
    def set_task(self, symbol: str, data: Dict[str, Any]) -> None: ...
    @abstractmethod
    def remove_task(self, symbol: str) -> None: ...
    @abstractmethod
    def all_tasks(self) -> Dict[str, Dict[str, Any]]: ...
    @abstractmethod
    def save(self) -> None: ...
    @abstractmethod
    def load(self) -> None: ...