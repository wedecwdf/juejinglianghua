# repository/core/state_gateway_impl.py
# -*- coding: utf-8 -*-
"""
StateGateway 简化版，仅作为内存数据容器。
所有持久化已迁移到各仓库，外部不应直接使用。
"""
from __future__ import annotations
from typing import Optional, Dict, Any, Set
from domain.day_data import DayData
from domain.board import BoardStatus, BoardBreakStatus, BoardCountData

class _StateGatewayImpl:
    _instance: Optional["_StateGatewayImpl"] = None

    def __new__(cls) -> "_StateGatewayImpl":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self.current_day_data: Dict[str, DayData] = {}
        self.total_buy_quantity: Dict[str, int] = {}
        self.total_sell_times: Dict[str, int] = {}
        self.board_status: Dict[str, BoardStatus] = {}
        self.board_count_data: Dict[str, BoardCountData] = {}
        self.board_break_status: Dict[str, BoardBreakStatus] = {}
        self.callback_addition_tasks: Dict[str, Dict[str, Any]] = {}
        self.dynamic_profit_next_day_adjustment_data: Dict[str, Dict[str, Any]] = {}
        self.pending_orders: Dict[str, Dict[str, Any]] = {}
        self.condition_triggers: Dict[str, Dict[str, Any]] = {}
        self.condition8_pending: Dict[str, Dict[str, str]] = {}
        self._cancelling_symbols: Set[str] = set()
        self._cancelled_symbols: Set[str] = set()
        self._sleep_state: bool = False