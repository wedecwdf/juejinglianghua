# repository/persistence/file_persistence.py
# -*- coding: utf-8 -*-
"""
独立的文件持久化工具，替代之前的 Mixin 继承模式。
提供 JSON 文件的读写能力，各仓库可在内部使用此工具。
"""
from __future__ import annotations
import json
import os
from datetime import datetime, date
from typing import Any, Dict, Optional


class FilePersistence:
    """封装 JSON 文件读写，自动创建目录，处理日期序列化"""

    @staticmethod
    def _json_default(obj: Any) -> str:
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        raise TypeError(f"Unsupported type: {type(obj)}")

    @staticmethod
    def load(file_path: str, default: Any = None) -> Any:
        """加载 JSON 文件，若不存在或异常则返回 default"""
        if not os.path.exists(file_path):
            return default
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载 {file_path} 失败: {e}")
            return default

    @staticmethod
    def save(file_path: str, data: Any) -> None:
        """保存数据到 JSON 文件，自动创建目录"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4, default=FilePersistence._json_default)
        except Exception as e:
            print(f"保存 {file_path} 失败: {e}")

    @staticmethod
    def remove(file_path: str) -> None:
        """删除指定文件"""
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"删除 {file_path} 失败: {e}")