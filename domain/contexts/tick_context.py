# domain/contexts/tick_context.py
# -*- coding: utf-8 -*-
""" 一次 tick 处理所需的完整上下文，替代全局单例。 """
from __future__ import annotations
from dataclasses import dataclass
from domain.stores import SessionRegistry, BoardStateRepository, CallbackTaskStore, OrderLedger
from config.strategy.config_objects import StrategyConfig

@dataclass
class TickContext:
    session_registry: SessionRegistry
    board_repo: BoardStateRepository
    callback_store: CallbackTaskStore
    order_ledger: OrderLedger
    config: StrategyConfig