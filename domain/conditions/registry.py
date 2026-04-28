# domain/conditions/registry.py
# -*- coding: utf-8 -*-
"""
条件注册表，通过装饰器收集所有 Condition 子类并按优先级排序。
"""
from __future__ import annotations
from typing import Type, List
from domain.decisions import Condition

class ConditionRegistry:
    _conditions: List[Type[Condition]] = []

    @classmethod
    def register(cls, priority: int):
        """装饰器：将 Condition 子类注册到表中，priority 越小优先级越高"""
        def wrapper(cond_cls: Type[Condition]):
            # 存储优先级和类引用
            cls._conditions.append((priority, cond_cls))
            # 按优先级排序（插入时排序也可以，但最终构建时排序更清晰）
            cls._conditions.sort(key=lambda x: x[0])
            return cond_cls
        return wrapper

    @classmethod
    def get_conditions(cls) -> List[Condition]:
        """返回按优先级排序的条件实例列表"""
        return [cond_cls() for _, cond_cls in cls._conditions]