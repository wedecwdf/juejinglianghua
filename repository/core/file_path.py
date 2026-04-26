# -*- coding: utf-8 -*-
"""
持久化文件路径集中管理
"""
from __future__ import annotations
import os

STORAGE_DIR = "json_storage"

def json_path(filename: str) -> str:
    return os.path.join(STORAGE_DIR, filename)

STATE_FILE = json_path("strategy_state.json")
PYRAMID_BASE_PRICE_FILE = json_path("callback_addition_tasks.json")  # 改为存储动态回调任务（替代原金字塔）
DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_FILE = json_path("dynamic_profit_next_day_adjustment.json")
PENDING_ORDERS_FILE = json_path("pending_orders.json")
CONDITION_TRIGGERS_FILE = json_path("condition_triggers.json")
BOARD_COUNT_FILE = json_path("board_count.json")