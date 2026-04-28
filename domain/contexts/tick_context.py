# domain/contexts/tick_context.py
from dataclasses import dataclass, field
from typing import Any, List
from domain.stores.context_store import ContextStore
from domain.stores.base import (
    AbstractSessionRegistry,
    AbstractBoardStateRepository,
    AbstractCallbackTaskStore,
    AbstractOrderLedger,
)
from config.strategy.config_objects import StrategyConfig
from domain.decisions import Condition

@dataclass
class TickContext:
    session_registry: AbstractSessionRegistry
    board_repo: AbstractBoardStateRepository
    callback_store: AbstractCallbackTaskStore
    order_ledger: AbstractOrderLedger
    config: StrategyConfig
    context_store: ContextStore
    conditions: List[Condition] = field(default_factory=list)
    side_effects: List[Condition] = field(default_factory=list)
    tick_time: Any = None