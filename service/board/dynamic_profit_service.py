# -*- coding: utf-8 -*-
"""
炸板动态止盈服务（状态机驱动）

原 board_service.py 中 handle_dynamic_profit_on_board_break 的独立拆分，
负责开板后的动态止盈状态流转与执行。
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from domain.board import BoardStatus, BoardBreakState
from domain.day_data import DayData
from config.strategy import DYNAMIC_PROFIT_ON_BOARD_BREAK_ENABLED
from .state_machine import BoardBreakContext, BoardBreakStateFactory


def handle_dynamic_profit_on_board_break(symbol: str, current_price: float,
                                        available_position: int, day_data: DayData,
                                        board_status: BoardStatus) -> Optional[int]:
    """
    炸板动态止盈 - 状态机驱动版

    状态流转：
    - STAGE1_MONITORING：仅监控跌破止盈线
    - STAGE2_TAKEOVER：监控再次封板、跌破止盈线、尾盘时间
    - TRIGGERED：已触发，不再执行
    """
    if not DYNAMIC_PROFIT_ON_BOARD_BREAK_ENABLED:
        return None

    # 获取当前状态
    current_state = board_status.get_break_state()

    # 已触发状态直接返回（一次性原则）
    if current_state == BoardBreakState.TRIGGERED:
        return None

    # 封板状态不执行（等待开板）
    if current_state == BoardBreakState.SEALED:
        return None

    # 创建状态机上下文
    ctx = BoardBreakContext(symbol, board_status, current_price,
                           datetime.now(), available_position)

    # 获取当前状态处理器并执行
    handler = BoardBreakStateFactory.create_state(current_state, ctx)
    result = handler.handle()

    # 清理day_data中的通用动态止盈标志（保持兼容）
    if result and result > 0:
        day_data.dynamic_profit_triggered = False
        day_data.dynamic_profit_high_price = -float("inf")
        day_data.dynamic_profit_line = -float("inf")

    return result