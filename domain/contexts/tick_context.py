# domain/contexts/tick_context.py
from dataclasses import dataclass, field
from typing import List, Any
from domain.stores.context_store import ContextStore
from domain.stores.base import AbstractSessionRegistry, AbstractBoardStateRepository, AbstractCallbackTaskStore
from domain.stores.order_interfaces import (
    OrderRepository,
    ConditionTriggerRepo,
    CancelLockManager,
    SleepStateManager,
    Condition8OrderTracker,
)
from config.strategy.config_objects import StrategyConfig
from domain.decisions import Condition

@dataclass
class TickContext:
    session_registry: AbstractSessionRegistry
    board_repo: AbstractBoardStateRepository
    callback_store: AbstractCallbackTaskStore
    # 拆分出的小接口，而非胖接口
    order_repo: OrderRepository
    condition_trigger_repo: ConditionTriggerRepo
    cancel_lock_manager: CancelLockManager
    sleep_state_manager: SleepStateManager
    condition8_tracker: Condition8OrderTracker
    context_store: ContextStore
    config: StrategyConfig
    conditions: List[Condition] = field(default_factory=list)
    side_effects: List[Condition] = field(default_factory=list)
    tick_time: Any = None