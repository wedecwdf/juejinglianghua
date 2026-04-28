# domain/contexts/tick_context.py
from dataclasses import dataclass
from domain.stores.context_store import ContextStore
from domain.stores.base import (
    AbstractSessionRegistry,
    AbstractBoardStateRepository,
    AbstractCallbackTaskStore,
    AbstractOrderLedger,
)
from config.strategy.config_objects import StrategyConfig

@dataclass
class TickContext:
    session_registry: AbstractSessionRegistry
    board_repo: AbstractBoardStateRepository
    callback_store: AbstractCallbackTaskStore
    order_ledger: AbstractOrderLedger
    config: StrategyConfig
    context_store: ContextStore