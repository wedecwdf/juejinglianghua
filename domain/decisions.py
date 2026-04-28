# domain/decisions.py
# -*- coding: utf-8 -*-
"""
决策管道核心：决策数据类、条件协议、仲裁器。
条件接口增加 is_side_effect、depends_on，evaluate 接收 shared_state。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class DecisionType(str, Enum):
    SELL = "sell"
    BUY = "buy"


@dataclass
class Decision:
    """单个条件产生的交易决策"""
    condition_name: str
    decision_type: DecisionType
    symbol: str
    price: float
    quantity: int
    reason: str
    price_offset: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)

    def apply(self, ctx) -> None:
        """子类重写以执行状态更新，ctx 是 TickContext"""
        pass


class Condition(ABC):
    """所有交易条件的统一接口"""
    # 类属性（由子类覆盖）
    condition_name: str = ""              # 唯一标识，如 'condition2'
    is_side_effect: bool = False          # True 表示只产生副作用，不参与仲裁
    depends_on: List[str] = field(default_factory=list)  # 依赖的其他条件名称

    @abstractmethod
    def evaluate(self, symbol: str, current_price: float, available_position: int,
                 day_data, base_price: float, ctx, shared_state: Dict[str, Any]) -> Optional[Decision]:
        """
        评估条件。
        shared_state: 由引擎在评估前收集的公共状态，包含 depends_on 中声明的条件的活跃状态。
        """
        ...


class DecisionArbiter:
    """决策仲裁器：按条件列表顺序返回第一个有效决策"""

    def __init__(self, conditions: list[Condition]):
        self.conditions = conditions

    def best_decision(self, symbol: str, current_price: float, available_position: int,
                      day_data, base_price: float, ctx, shared_state: Dict[str, Any]) -> Optional[Decision]:
        for cond in self.conditions:
            decision = cond.evaluate(symbol, current_price, available_position,
                                     day_data, base_price, ctx, shared_state)
            if decision is not None:
                return decision
        return None