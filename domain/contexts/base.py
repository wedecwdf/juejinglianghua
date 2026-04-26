# domain/contexts/base.py
# -*- coding: utf-8 -*-
"""所有条件上下文的基类，提供持久化接口"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseConditionContext(ABC):
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        ...

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseConditionContext':
        ...