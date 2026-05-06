# domain/contexts/tick_context.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Any, Optional
from datetime import datetime

from domain.stores.context_store import ContextStore
from domain.stores.base import (
    AbstractSessionRegistry,
    AbstractBoardStateRepository,
    AbstractCallbackTaskStore,
)
from domain.stores.order_interfaces import (
    OrderRepository,
    ConditionTriggerRepo,
    CancelLockManager,
    SleepStateManager,
    Condition8OrderTracker,
)
from config.strategy.config_objects import Condition8Config, TechIndicatorConfig
from domain.decisions import Condition


@dataclass
class TickContext:
    session_registry: AbstractSessionRegistry
    board_repo: AbstractBoardStateRepository
    callback_store: AbstractCallbackTaskStore

    order_repo: OrderRepository
    condition_trigger_repo: ConditionTriggerRepo
    cancel_lock_manager: CancelLockManager
    sleep_state_manager: SleepStateManager
    condition8_tracker: Condition8OrderTracker

    context_store: ContextStore

    # 仅保留大量条件用到的配置片段，而不是整个 StrategyConfig
    condition8_config: Condition8Config
    tech_indicator_config: TechIndicatorConfig   # 用于指标刷新和历史数据加载

    conditions: List[Condition] = field(default_factory=list)
    side_effects: List[Condition] = field(default_factory=list)

    tick_time: Optional[datetime] = None