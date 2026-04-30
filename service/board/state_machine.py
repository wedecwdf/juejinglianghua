# service/board/state_machine.py
# -*- coding: utf-8 -*-
"""
炸板动态止盈状态机与板数工具函数，参数从 BoardConfig 获取。
"""
from __future__ import annotations
import logging
from datetime import datetime, time as dt_time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from domain.board import BoardStatus, BoardBreakState
from config.strategy.config_objects import BoardConfig

logger = logging.getLogger(__name__)

# 默认配置，可在调用时被覆盖
_board_config = BoardConfig()


def set_default_board_config(config: BoardConfig):
    global _board_config
    _board_config = config


class BoardBreakContext:
    def __init__(self, symbol: str, board_status: BoardStatus,
                 current_price: float, tick_time: datetime,
                 available_position: int, config: BoardConfig = None):
        self.symbol = symbol
        self.board_status = board_status
        self.current_price = current_price
        self.tick_time = tick_time
        self.available_position = available_position
        self.config = config or _board_config
        self.sell_qty: Optional[int] = None


class BoardBreakStateHandler(ABC):
    def __init__(self, context: BoardBreakContext):
        self.ctx = context

    @abstractmethod
    def handle(self) -> Optional[int]:
        pass

    @abstractmethod
    def can_transition_to(self, new_state: BoardBreakState) -> bool:
        pass


class SealedState(BoardBreakStateHandler):
    def handle(self) -> Optional[int]:
        return None

    def can_transition_to(self, new_state: BoardBreakState) -> bool:
        return new_state in [BoardBreakState.STAGE1_MONITORING, BoardBreakState.TRIGGERED]


class Stage1MonitoringState(BoardBreakStateHandler):
    def handle(self) -> Optional[int]:
        bs = self.ctx.board_status
        if self.ctx.current_price <= bs.board_break_dynamic_profit_line:
            sell_qty = int(self.ctx.available_position *
                           self.ctx.config.dynamic_profit_break_line_sell_percent)
            sell_qty = (sell_qty // 100) * 100
            if sell_qty > 0:
                bs.set_break_state(BoardBreakState.TRIGGERED)
                logger.info("【状态机：STAGE1->TRIGGERED】%s 阶段①触发跌破止盈线卖出，基准价:%.4f，卖出%d股",
                            self.ctx.symbol, bs.last_effective_limit_up_price, sell_qty)
                return sell_qty
        return None

    def can_transition_to(self, new_state: BoardBreakState) -> bool:
        return new_state in [BoardBreakState.TRIGGERED, BoardBreakState.STAGE2_TAKEOVER]


class Stage2TakeoverState(BoardBreakStateHandler):
    def handle(self) -> Optional[int]:
        bs = self.ctx.board_status
        current_time = self.ctx.tick_time.time()
        no_action_time = _parse_time_string(self.ctx.config.no_action_sell_time)

        if bs.is_sealed and bs.effective_sealed:
            sell_qty = int(self.ctx.available_position *
                           self.ctx.config.dynamic_profit_sealed_sell_percent)
            sell_qty = (sell_qty // 100) * 100
            if sell_qty > 0:
                bs.set_break_state(BoardBreakState.TRIGGERED)
                logger.info("【状态机：STAGE2->TRIGGERED】%s 阶段②-再次封板卖出，基准价:%.4f，卖出%d股",
                            self.ctx.symbol, bs.last_effective_limit_up_price, sell_qty)
                return sell_qty

        if self.ctx.current_price <= bs.board_break_dynamic_profit_line:
            sell_qty = int(self.ctx.available_position *
                           self.ctx.config.dynamic_profit_break_line_sell_percent)
            sell_qty = (sell_qty // 100) * 100
            if sell_qty > 0:
                bs.set_break_state(BoardBreakState.TRIGGERED)
                logger.info("【状态机：STAGE2->TRIGGERED】%s 阶段②-跌破止盈线卖出（接管），基准价:%.4f，卖出%d股",
                            self.ctx.symbol, bs.last_effective_limit_up_price, sell_qty)
                return sell_qty

        if current_time >= no_action_time:
            sell_qty = int(self.ctx.available_position *
                           self.ctx.config.dynamic_profit_no_action_sell_percent)
            sell_qty = (sell_qty // 100) * 100
            if sell_qty > 0:
                bs.set_break_state(BoardBreakState.TRIGGERED)
                logger.info("【状态机：STAGE2->TRIGGERED】%s 阶段②-尾盘无动作卖出，基准价:%.4f，卖出%d股",
                            self.ctx.symbol, bs.last_effective_limit_up_price, sell_qty)
                return sell_qty
        return None

    def can_transition_to(self, new_state: BoardBreakState) -> bool:
        return new_state in [BoardBreakState.TRIGGERED]


class TriggeredState(BoardBreakStateHandler):
    def handle(self) -> Optional[int]:
        return None

    def can_transition_to(self, new_state: BoardBreakState) -> bool:
        return False


class BoardBreakStateFactory:
    @staticmethod
    def create_state(state: BoardBreakState,
                     context: BoardBreakContext) -> BoardBreakStateHandler:
        state_map = {
            BoardBreakState.SEALED: SealedState,
            BoardBreakState.STAGE1_MONITORING: Stage1MonitoringState,
            BoardBreakState.STAGE2_TAKEOVER: Stage2TakeoverState,
            BoardBreakState.TRIGGERED: TriggeredState
        }
        handler_class = state_map.get(state)
        if handler_class:
            return handler_class(context)
        raise ValueError(f"未知状态: {state}")


def _parse_time_string(time_str: str) -> dt_time:
    try:
        hour, minute = map(int, time_str.split(':'))
        return dt_time(hour, minute)
    except Exception:
        return dt_time(14, 55)


def _ensure_datetime(t: Any) -> Optional[datetime]:
    if isinstance(t, datetime):
        return t
    if isinstance(t, str):
        try:
            return datetime.fromisoformat(t)
        except Exception:
            return None
    return None


def get_limit_up_percent(symbol: str, config: BoardConfig = None) -> float:
    if config is None:
        config = _board_config
    if symbol.startswith("SHSE.60") or symbol.startswith("SZSE.00"):
        return config.main_board_limit_up
    if symbol.startswith("SZSE.30") or symbol.startswith("SHSE.688"):
        return config.gem_board_limit_up
    if "ST" in symbol or "*ST" in symbol:
        return config.st_board_limit_up
    if symbol.startswith("BSE."):
        return config.bse_board_limit_up
    return config.main_board_limit_up


def is_limit_up_price(current_price: float, limit_up_price: float,
                      prev_close: float, config: BoardConfig = None) -> bool:
    if config is None:
        config = _board_config
    if prev_close <= 0:
        return False
    tolerance = prev_close * config.limit_up_tolerance
    return (limit_up_price - tolerance) <= current_price <= (limit_up_price + tolerance)