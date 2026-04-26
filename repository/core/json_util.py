# repository/core/json_util.py
# -*- coding: utf-8 -*-
"""JSON 序列化/反序列化公共工具"""
from __future__ import annotations
import json
import os
from datetime import datetime, date
from typing import Any, Dict

def json_default(o: Any) -> str:
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    raise TypeError(f"Unsupported type: {type(o)}")

def save_json(file_path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=json_default)

def load_json(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)