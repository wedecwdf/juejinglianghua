# repository/stores/callback_task_store_impl.py
# -*- coding: utf-8 -*-
"""
动态回调加仓任务仓库实现，不依赖 StateGateway，直接操作内存字典和文件。
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.stores.base import AbstractCallbackTaskStore
from repository.persistence.file_persistence import FilePersistence
from repository.core.file_path import PYRAMID_BASE_PRICE_FILE  # 复用路径


class CallbackTaskStoreImpl(AbstractCallbackTaskStore):
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._persistence = FilePersistence()

    def get_task(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self._tasks.get(symbol)

    def set_task(self, symbol: str, data: Dict[str, Any]) -> None:
        self._tasks[symbol] = data

    def remove_task(self, symbol: str) -> None:
        self._tasks.pop(symbol, None)

    def all_tasks(self) -> Dict[str, Dict[str, Any]]:
        return self._tasks

    def save(self) -> None:
        data_to_save = {
            "callback_addition_tasks": self._tasks,
            "_comment": "动态回调加仓任务（替代原金字塔加仓）",
        }
        self._persistence.save(PYRAMID_BASE_PRICE_FILE, data_to_save)

    def load(self) -> None:
        data = self._persistence.load(PYRAMID_BASE_PRICE_FILE)
        if data and "callback_addition_tasks" in data:
            self._tasks = data["callback_addition_tasks"]