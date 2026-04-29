# service/board/dynamic_profit_service.py
# -*- coding: utf-8 -*-
"""
炸板动态止盈服务（状态机驱动）
修改：使用 ContextStore 获取条件上下文，移除对 SessionRegistry 的非法调用。
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional
from domain.board import BoardStatus, BoardBreakState
from domain.day_data import DayData
from domain.stores.context_store import ContextStore
from config.strategy import DYNAMIC_PROFIT_ON_BOARD_BREAK_ENABLED
from .state_machine import BoardBreakContext, BoardBreakStateFactory

logger = logging.getLogger(__name__)


def handle_dynamic_profit_on_board_break(symbol: str, current_price: float,
                                         available_position: int, day_data: DayData,
                                         board_status: BoardStatus,
                                         context_store: ContextStore = None) -> Optional[int]:
    if not DYNAMIC_PROFIT_ON_BOARD_BREAK_ENABLED:
        return None

    current_state = board_status.get_break_state()
    if current_state == BoardBreakState.TRIGGERED:
        return None
    if current_state == BoardBreakState.SEALED:
        return None

    ctx = BoardBreakContext(symbol, board_status, current_price,
                            datetime.now(), available_position)
    handler = BoardBreakStateFactory.create_state(current_state, ctx)
    result = handler.handle()

    # 炸板卖出后，清理条件2、条件9的监控标志
    if result and result > 0:
        if context_store:
            try:
                ctx2 = context_store.get('condition2', symbol)
                ctx2.dynamic_profit_triggered = False
                ctx2.dynamic_profit_high_price = -float("inf")
                ctx2.dynamic_profit_line = -float("inf")
            except KeyError:
                pass
            try:
                ctx9 = context_store.get('condition9', symbol)
                ctx9.condition9_triggered = False
                ctx9.condition9_high_price = -float('inf')
                ctx9.condition9_profit_line = -float('inf')
            except KeyError:
                pass
    return result