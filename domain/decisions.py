# domain/decisions.py
# -*- coding: utf-8 -*-
"""
决策管道核心定义：决策数据类、条件协议、仲裁器。
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
    condition_name: str          # 例如 'condition2', 'next_day_stop_loss'
    decision_type: DecisionType
    symbol: str
    price: float
    quantity: int
    reason: str
    price_offset: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)   # 触发器数据等


class Condition(ABC):
    """所有交易条件的统一接口"""
    @abstractmethod
    def evaluate(self, symbol: str, current_price: float, available_position: int,
                 day_data, base_price, ctx) -> Optional[Decision]:
        """
        评估条件，若触发则返回 Decision，否则返回 None。
        day_data 和 ctx 分别是行情快照和 TickContext。
        """
        ...


class DecisionArbiter:
    """决策仲裁器：按优先级顺序返回第一个有效决策"""

    def __init__(self, conditions: list[Condition]):
        self.conditions = conditions

    def best_decision(self, symbol: str, current_price: float, available_position: int,
                      day_data, base_price: float, ctx) -> Optional[Decision]:
        """依次执行条件，返回第一个非 None 的决策（即最高优先级触发项）"""
        for cond in self.conditions:
            decision = cond.evaluate(symbol, current_price, available_position,
                                     day_data, base_price, ctx)
            if decision is not None:
                return decision
        return None