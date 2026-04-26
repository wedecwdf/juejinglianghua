# repository/core/serializer.py
# -*- coding: utf-8 -*-
"""
JSON 序列化与对象Slots转换工具
"""
from __future__ import annotations
import json
from datetime import datetime, date
from typing import Any, Dict


def _json_default(o: Any) -> str:
    """datetime/date -> ISO 字符串"""
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    raise TypeError(f"Unsupported type: {type(o)}")


def _slots_to_dict(obj) -> Dict[str, Any]:
    """将带有 __slots__ 的对象转为字典"""
    return {slot: getattr(obj, slot) for slot in obj.__slots__}


def _dict_to_slots(cls, d: Dict[str, Any]):
    """将字典填充到带有 __slots__ 的对象"""
    obj = cls.__new__(cls)
    for slot in cls.__slots__:
        setattr(obj, slot, d.get(slot, None))
    return obj