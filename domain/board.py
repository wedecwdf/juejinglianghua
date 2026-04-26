# domain/board.py
# -*- coding: utf-8 -*-
"""
板数、断板、炸板 纯数据结构

【状态机形式化梳理】
1. 移除 RESEALED 伪状态（重新封板直接回到 SEALED）
2. 删除 BoardStatus 中冗余的旧布尔字段（board_break_stage1_activated 等）
3. 以 _board_break_state 作为炸板动态止盈的唯一事实来源
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Optional, Dict, Any
from enum import Enum, auto


class BoardBreakState(Enum):
    """
    炸板动态止盈显式状态枚举（4状态，移除伪状态 RESEALED）
    """
    SEALED = "sealed"  # 封板中（初始状态）
    STAGE1_MONITORING = "stage1"  # 阶段①：开板立即触发机制（监控中）
    STAGE2_TAKEOVER = "stage2"  # 阶段②：炸板确认接管机制（接管中）
    TRIGGERED = "triggered"  # 已触发（成功成交，当日结束）


class BoardStatus:
    __slots__ = (
        'limit_up_price', 'sealed_start_time', 'opened_start_time',
        'is_sealed', 'is_opened', 'prev_close', 'effective_sealed',
        'dynamic_profit_activated', 'last_limit_up_time', 'sealed_count',
        'break_count', 'first_board_date', 'first_board_close_price',
        'is_first_board_sealed', 'last_effective_sealed_date',
        'today_effective_sealed', 'today_open_price',
        'last_effective_limit_up_price',  # 炸板动态止盈基准价（锁定涨停价）
        'board_break_start_time',  # 阶段②超时计算起点
        'board_break_dynamic_profit_line',  # 动态止盈线（数据字段）
        '_board_break_state'  # 唯一状态事实来源（字符串，兼容JSON）
    )

    def __init__(self) -> None:
        self.limit_up_price: float = 0
        self.sealed_start_time: Optional[datetime] = None
        self.opened_start_time: Optional[datetime] = None
        self.is_sealed: bool = False
        self.is_opened: bool = False
        self.prev_close: float = 0
        self.effective_sealed: bool = False
        self.dynamic_profit_activated: bool = False
        self.last_limit_up_time: Optional[datetime] = None
        self.sealed_count: int = 0
        self.break_count: int = 0
        self.first_board_date: Optional[date] = None
        self.first_board_close_price: float = 0
        self.is_first_board_sealed: bool = False
        self.last_effective_sealed_date: Optional[date] = None
        self.today_effective_sealed: bool = False
        self.today_open_price: Optional[float] = None
        self.last_effective_limit_up_price: float = 0.0
        self.board_break_start_time: Optional[datetime] = None
        self.board_break_dynamic_profit_line: float = 0.0
        self._board_break_state: str = BoardBreakState.SEALED.value

    # ------------------ 状态机辅助方法 ------------------
    def get_break_state(self) -> BoardBreakState:
        """
        获取当前炸板动态止盈状态。
        兼容旧数据：若 _board_break_state 缺失或异常，默认返回 SEALED
        """
        if self._board_break_state is None:
            self._board_break_state = BoardBreakState.SEALED.value

        if isinstance(self._board_break_state, str):
            try:
                return BoardBreakState(self._board_break_state)
            except ValueError:
                return BoardBreakState.SEALED

        if isinstance(self._board_break_state, BoardBreakState):
            return self._board_break_state

        return BoardBreakState.SEALED

    def set_break_state(self, state: BoardBreakState) -> None:
        """
        设置炸板动态止盈状态，存储为字符串以兼容JSON序列化。
        单一事实来源：仅修改 _board_break_state，不再同步冗余布尔字段。
        """
        if state is None:
            return
        self._board_break_state = state.value


class BoardBreakStatus:
    __slots__ = (
        'board_break_triggered', 'static_stop_loss_activated',
        'dynamic_profit_activated', 'static_stop_loss_price',
        'dynamic_profit_high_price', 'dynamic_profit_line',
        'board_break_date', 'first_board_close_price', 'sold',
        'prev_effective_sealed_date'
    )

    def __init__(self) -> None:
        self.board_break_triggered: bool = False
        self.static_stop_loss_activated: bool = False
        self.dynamic_profit_activated: bool = False
        self.static_stop_loss_price: float = 0
        self.dynamic_profit_high_price: float = -float('inf')
        self.dynamic_profit_line: float = -float('inf')
        self.board_break_date: Optional[date] = None
        self.first_board_close_price: float = 0
        self.sold: bool = False
        self.prev_effective_sealed_date: Optional[date] = None


class BoardCountData:
    __slots__ = (
        'start_date', 'count', 'prev_close', 'limit_up_price',
        'last_updated', 'effective_sealed'
    )

    def __init__(self) -> None:
        self.start_date: str = ''
        self.count: int = 0
        self.prev_close: float = 0
        self.limit_up_price: float = 0
        self.last_updated: str = ''
        self.effective_sealed: bool = False