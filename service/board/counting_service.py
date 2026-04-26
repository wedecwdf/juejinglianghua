# -*- coding: utf-8 -*-
"""
板数计数服务

【状态机形式化梳理】
1. 移除 RESEALED 伪状态，重新封板直接回到 SEALED
2. 删除 board_break_confirmed 布尔字段引用，以状态本身判断避免重复转换
"""
from __future__ import annotations
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

def handle_board_counting(symbol: str, current_price: float,
                          prev_close: float, tick_time: datetime,
                          board_status: BoardStatus,
                          board_count_data: Optional[BoardCountData]) -> Optional[BoardCountData]:
    """
    板数计数与炸板状态机驱动

    状态转换触发点：
    - 涨停（封板）：驱动到 SEALED
    - 开板：驱动到 STAGE1_MONITORING
    - 开板超时：驱动到 STAGE2_TAKEOVER
    - 重新封板：从 STAGE1/STAGE2 直接回到 SEALED
    """
    if not BOARD_COUNTING_ENABLED or prev_close <= 0:
        return board_count_data

    limit_up_percent = get_limit_up_percent(symbol)
    limit_up_price = round(prev_close * (1 + limit_up_percent), 2)
    board_status.limit_up_price = limit_up_price
    board_status.prev_close = prev_close

    # 获取当前状态
    current_state = board_status.get_break_state()

    if is_limit_up_price(current_price, limit_up_price, prev_close):
        # ==================== 涨停（封板）逻辑 ====================
        # 处理重新封板（从开板回到封板）
        if board_status.is_opened:
            board_status.is_opened = False
            board_status.opened_start_time = None
            # 从STAGE1或STAGE2重新封板：直接回到SEALED
            if current_state in [BoardBreakState.STAGE1_MONITORING,
                                  BoardBreakState.STAGE2_TAKEOVER]:
                board_status.set_break_state(BoardBreakState.SEALED)
                print(f"【状态机】{symbol} "
                      f"重新封板，当前状态:{current_state.value}->SEALED，阶段①/②暂停，下次开板重新激活")

        # 处理封板数据（原有逻辑保持不变）
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
            # 锁定炸板动态止盈基准价（首次涨停价）
            board_status.last_effective_limit_up_price = limit_up_price
            # 状态机：确保在SEALED状态
            if board_status.get_break_state() != BoardBreakState.SEALED:
                board_status.set_break_state(BoardBreakState.SEALED)
            print(f"【首板】{symbol} 首次涨停，涨停价 {limit_up_price:.4f} 已锁定")
        else:
            last_date = datetime.fromisoformat(
                board_count_data.last_updated).date()
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
                # 连板：新的一天，重置状态机
                board_count_data.count += 1
                board_count_data.limit_up_price = current_price
                board_count_data.last_updated = tick_time.isoformat()
                board_count_data.effective_sealed = False
                board_status.sealed_start_time = tick_time
                board_status.is_sealed = True
                board_status.effective_sealed = False
                board_status.today_effective_sealed = False
                # 连板时更新基准价
                board_status.last_effective_limit_up_price = limit_up_price
                # 重置状态机到新交易日
                board_status.set_break_state(BoardBreakState.SEALED)
                print(f"【连板】{symbol} 第{board_count_data.count}板，"
                      f"新基准价 {limit_up_price:.4f}，状态机重置")
        return board_count_data

    # ==================== 非涨停（开板）逻辑 ====================
    if board_count_data is not None:
        if not board_status.is_opened:
            # -------------- 首次开板 --------------
            board_status.is_opened = True
            board_status.opened_start_time = tick_time
            board_status.is_sealed = False
            # 状态机：SEALED -> STAGE1（如果未触发过）
            if BOARD_BREAK_STAGE1_ENABLED and current_state == BoardBreakState.SEALED:
                board_status.set_break_state(BoardBreakState.STAGE1_MONITORING)
                board_status.board_break_start_time = tick_time
                # 计算止盈线（基于锁定涨停价）
                locked_base = board_status.last_effective_limit_up_price
                board_status.board_break_dynamic_profit_line = locked_base * (
                    1 - BOARD_BREAK_DYNAMIC_PROFIT_DECLINE_PERCENT)
                print(f"【状态机：SEALED->STAGE1】{symbol} 首次开板，阶段①激活，"
                      f"基准价:{locked_base:.4f}，"
                      f"止盈线:{board_status.board_break_dynamic_profit_line:.4f}")
        else:
            # -------------- 持续开板：检查阶段②接管 --------------
            if BOARD_BREAK_STAGE2_ENABLED and current_state == BoardBreakState.STAGE1_MONITORING:
                opened_start = _ensure_datetime(board_status.opened_start_time)
                if opened_start is not None:
                    opened_duration = (tick_time - opened_start).total_seconds() / 60
                    if opened_duration >= MAX_OPEN_DURATION:
                        # 避免重复转换：仅在当前仍是STAGE1时执行
                        if board_status.get_break_state() == BoardBreakState.STAGE1_MONITORING:
                            board_status.set_break_state(BoardBreakState.STAGE2_TAKEOVER)
                            print(f"【状态机：STAGE1->STAGE2】{symbol} "
                                  f"开板持续{opened_duration:.1f}分钟，"
                                  f"炸板确认，阶段②接管，阶段①休眠")
        return board_count_data