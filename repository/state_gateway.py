# repository/state_gateway.py
# -*- coding: utf-8 -*-
"""
持久化网关统一入口（拆分版）

所有旧 import 仍指向这里，保证零改动兼容
"""

from __future__ import annotations
from typing import Optional

# 从正确的源导入 json_path，并作为 _json_path 别名导出，保持向后兼容
from repository.core.file_path import json_path as _json_path
from repository.core.state_gateway_impl import _StateGatewayImpl

class StateGateway:
    """透明代理：所有方法/属性直接映射到真正的单例"""
    def __init__(self) -> None:
        self._impl = _StateGatewayImpl()

    def __getattr__(self, name: str):
        return getattr(self._impl, name)