# service/board/counting_service.py
# -*- coding: utf-8 -*-
"""
板数计数服务
所有 print 替换为 logger。
"""
from __future__ import annotations
import logging
from datetime import datetime, date
from typing import Optional
from domain.board import BoardStatus, BoardCountData, BoardBreakState
from config.strategy import (
    BOARD_COUNTING_ENABLED,
    MIN_SEALED_DURATION,
    MAX_OPEN_DURATION,
    BOARD_BREAK_STAGE1_ENABLED,
    BOARD_BREAK_STAGE2_ENABLED,
    DYNAMIC_PROFIT_ON_BOARD_BREAK_ENABLED,
    BOARD_BREAK_DYNAMIC_PROFIT_DECLINE_PERCENT
)
from .state_machine import (
    BoardBreakContext,
    BoardBreakStateFactory,
    get_limit_up_percent,
    is_limit_up_price,
    _ensure_datetime
)

logger = logging.getLogger(__name__)

def handle_board_counting(symbol: str, current_price: float,
                          prev_close: float, tick_time: datetime,
                          board_status: BoardStatus,
                          board_count_data: Optional[BoardCountData]) -> Optional[BoardCountData]:
    if not BOARD_COUNTING_ENABLED or prev_close <= 0:
        return board_count_data

    limit_up_percent = get_limit_up_percent(symbol)
    limit_up_price = round(prev_close * (1 + limit_up_percent), 2)
    board_status.limit_up_price = limit_up_price
    board_status.prev_close = prev_close

    current_state = board_status.get_break_state()

    if is_limit_up_price(current_price, limit_up_price, prev_close):
        # 涨停（封板）逻辑
        if board_status.is_opened:
            board_status.is_opened = False
            board_status.opened_start_time = None
            if current_state in [BoardBreakState.STAGE1_MONITORING, BoardBreakState.STAGE2_TAKEOVER]:
                board_status.set_break_state(BoardBreakState.SEALED)
                logger.info("【状态机】%s 重新封板，当前状态:%s->SEALED，阶段①/②暂停", symbol, current_state.value)

        if board_count_data is None:
            board_count_data = BoardCountData()
            board_count_data.start_date = tick_time.date().isoformat()
            board_count_data.count = 1
            board_count_data.prev_close = prev_close
            board_count_data.limit_up_price = current_price
            board_count_data.last_updated = tick_time.isoformat()
            board_count_data.effective_sealed = False
            board_status.sealed_start_time = tick_time
            board_status.is_sealed = True
            board_status.effective_sealed = False
            board_status.last_limit_up_time = tick_time
            board_status.today_effective_sealed = False
            board_status.last_effective_limit_up_price = limit_up_price
            if board_status.get_break_state() != BoardBreakState.SEALED:
                board_status.set_break_state(BoardBreakState.SEALED)
            logger.info("【首板】%s 首次涨停，涨停价 %.4f 已锁定", symbol, limit_up_price)
        else:
            last_date = datetime.fromisoformat(board_count_data.last_updated).date()
            if tick_time.date() == last_date:
                if not board_status.effective_sealed and board_status.sealed_start_time:
                    sealed_duration = (tick_time - board_status.sealed_start_time).total_seconds() / 60
                    if sealed_duration >= MIN_SEALED_DURATION:
                        board_status.effective_sealed = True
                        board_status.today_effective_sealed = True
                        board_status.last_effective_sealed_date = tick_time.date()
                        board_count_data.effective_sealed = True
                        board_count_data.limit_up_price = current_price
                        board_count_data.last_updated = tick_time.isoformat()
            else:
                # 连板
                board_count_data.count += 1
                board_count_data.limit_up_price = current_price
                board_count_data.last_updated = tick_time.isoformat()
                board_count_data.effective_sealed = False
                board_status.sealed_start_time = tick_time
                board_status.is_sealed = True
                board_status.effective_sealed = False
                board_status.today_effective_sealed = False
                board_status.last_effective_limit_up_price = limit_up_price
                board_status.set_break_state(BoardBreakState.SEALED)
                logger.info("【连板】%s 第%d板，新基准价 %.4f，状态机重置", symbol, board_count_data.count, limit_up_price)
        return board_count_data

    # 非涨停（开板）逻辑
    if board_count_data is not None:
        if not board_status.is_opened:
            board_status.is_opened = True
            board_status.opened_start_time = tick_time
            board_status.is_sealed = False
            if BOARD_BREAK_STAGE1_ENABLED and current_state == BoardBreakState.SEALED:
                board_status.set_break_state(BoardBreakState.STAGE1_MONITORING)
                board_status.board_break_start_time = tick_time
                locked_base = board_status.last_effective_limit_up_price
                board_status.board_break_dynamic_profit_line = locked_base * (
                    1 - BOARD_BREAK_DYNAMIC_PROFIT_DECLINE_PERCENT)
                logger.info("【状态机：SEALED->STAGE1】%s 首次开板，阶段①激活，"
                             "基准价:%.4f，止盈线:%.4f",
                             symbol, locked_base, board_status.board_break_dynamic_profit_line)
        else:
            if BOARD_BREAK_STAGE2_ENABLED and current_state == BoardBreakState.STAGE1_MONITORING:
                opened_start = _ensure_datetime(board_status.opened_start_time)
                if opened_start is not None:
                    opened_duration = (tick_time - opened_start).total_seconds() / 60
                    if opened_duration >= MAX_OPEN_DURATION:
                        if board_status.get_break_state() == BoardBreakState.STAGE1_MONITORING:
                            board_status.set_break_state(BoardBreakState.STAGE2_TAKEOVER)
                            logger.info("【状态机：STAGE1->STAGE2】%s "
                                         "开板持续%.1f分钟，炸板确认，阶段②接管",
                                         symbol, opened_duration)
    return board_count_data