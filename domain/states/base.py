# -*- coding: utf-8 -*-
"""
状态对象基类

提供统一的序列化、反序列化接口。
"""

from __future__ import annotations
from typing import Dict, Any


class BaseState:
    """所有业务状态子对象的基类"""

    __slots__ = ()

    def to_dict(self) -> Dict[str, Any]:
        """将自身所有字段导出为字典"""
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def from_dict(self, data: Dict[str, Any]) -> None:
        """从字典加载数据（仅覆盖存在的字段，保持默认值不变）"""
        for slot in self.__slots__:
            if slot in data:
                setattr(self, slot, data[slot])