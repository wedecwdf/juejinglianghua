# domain/stores/context_store.py
# -*- coding: utf-8 -*-
"""
通用条件上下文存储，替代 SessionRegistry 的硬编码 getter。
每个条件按名称和 symbol 存取自己的上下文对象。
"""
from __future__ import annotations
from typing import Any, Callable, Dict

class ContextStore:
    def __init__(self):
        self._contexts: Dict[str, Dict[str, Any]] = {}

    def get(self, condition_name: str, symbol: str, factory: Callable[[], Any] = None):
        """获取指定条件的上下文，不存在时使用 factory 创建（若提供）"""
        if condition_name not in self._contexts:
            self._contexts[condition_name] = {}
        ctx_map = self._contexts[condition_name]
        if symbol not in ctx_map:
            if factory:
                ctx_map[symbol] = factory()
            else:
                raise KeyError(f"上下文不存在: {condition_name}:{symbol}")
        return ctx_map[symbol]

    def set(self, condition_name: str, symbol: str, ctx: Any):
        if condition_name not in self._contexts:
            self._contexts[condition_name] = {}
        self._contexts[condition_name][symbol] = ctx