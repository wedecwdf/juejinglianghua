# domain/decisions.py
# -*- coding: utf-8 -*-
"""
决策管道核心：决策数据类、条件协议、仲裁器、以及支持自更新的 PatchedDecision。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
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
        """
        子类可重写以实现状态更新。默认空操作。
        ctx 是 TickContext。
        """
        pass


class Condition(ABC):
    """所有交易条件的统一接口"""
    @abstractmethod
    def evaluate(self, symbol: str, current_price: float, available_position: int,
                 day_data, base_price: float, ctx) -> Optional[Decision]:
        ...


class DecisionArbiter:
    """决策仲裁器：按条件列表顺序返回第一个有效决策"""

    def __init__(self, conditions: list[Condition]):
        self.conditions = conditions

    def best_decision(self, symbol: str, current_price: float, available_position: int,
                      day_data, base_price: float, ctx) -> Optional[Decision]:
        for cond in self.conditions:
            decision = cond.evaluate(symbol, current_price, available_position,
                                     day_data, base_price, ctx)
            if decision is not None:
                return decision
        return None