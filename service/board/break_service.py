# -*- coding: utf-8 -*-
"""
断板机制服务（静态止损）

原 board_service.py 中 handle_board_break_mechanism 的独立拆分，
负责次日低开判断与静态止损执行。
"""
from __future__ import annotations
from datetime import datetime, date, timedelta
from typing import Optional

from domain.board import BoardStatus, BoardBreakStatus
from config.strategy import (
    BOARD_BREAK_ENABLED,
    BOARD_BREAK_STATIC_STOP_LOSS_PERCENT,
    BOARD_BREAK_DYNAMIC_PROFIT_DECLINE_PERCENT,
    BOARD_BREAK_SELL_PERCENT,
    BOARD_BREAK_PRICE_OFFSET
)
from .state_machine import is_limit_up_price


def handle_board_break_mechanism(symbol: str, current_price: float,
                                prev_close: float, tick_time: datetime,
                                board_status: BoardStatus,
                                board_break_status: BoardBreakStatus,
                                available_position: int) -> Optional[int]:
    """断板机制（静态止损）- 独立于状态机体系"""
    if not BOARD_BREAK_ENABLED:
        return None

    if board_break_status.sold:
        return None

    last_effective = board_status.last_effective_sealed_date
    if last_effective is None:
        return None

    next_trading_day = last_effective
    for _ in range(30):
        next_trading_day += timedelta(days=1)
        if next_trading_day.weekday() < 5:
            break

    if tick_time.date() != next_trading_day:
        return None

    if board_status.today_effective_sealed:
        print(f"【断板判定】{symbol} 当日曾经有效涨停过，不算断板")
        return None

    if is_limit_up_price(current_price, board_status.limit_up_price, prev_close):
        return None

    if not board_break_status.board_break_triggered:
        board_break_status.board_break_triggered = True
        board_break_status.board_break_date = tick_time.date()
        board_break_status.prev_effective_sealed_date = last_effective
        board_break_status.first_board_close_price = board_status.first_board_close_price

        static_stop_loss_price = prev_close * (1 - BOARD_BREAK_STATIC_STOP_LOSS_PERCENT)
        board_break_status.static_stop_loss_price = static_stop_loss_price
        board_break_status.static_stop_loss_activated = True
        board_break_status.dynamic_profit_activated = True
        board_break_status.dynamic_profit_high_price = current_price
        board_break_status.dynamic_profit_line = current_price * (
            1 - BOARD_BREAK_DYNAMIC_PROFIT_DECLINE_PERCENT)

        print(f"【断板触发】{symbol} 静态止损和动态止盈同时激活")

    if current_price > board_break_status.dynamic_profit_high_price:
        board_break_status.dynamic_profit_high_price = current_price
        board_break_status.dynamic_profit_line = current_price * (
            1 - BOARD_BREAK_DYNAMIC_PROFIT_DECLINE_PERCENT)

    if current_price <= board_break_status.static_stop_loss_price + BOARD_BREAK_PRICE_OFFSET:
        if not board_break_status.sold:
            sell_qty = int(available_position * BOARD_BREAK_SELL_PERCENT)
            sell_qty = (sell_qty // 100) * 100
            if sell_qty > 0:
                board_break_status.sold = True
                print(f"【断板静态止损】{symbol} 卖出{sell_qty}股")
                return sell_qty

    if (board_break_status.dynamic_profit_activated and
            current_price <= board_break_status.dynamic_profit_line):
        if not board_break_status.sold:
            sell_qty = int(available_position * BOARD_BREAK_SELL_PERCENT)
            sell_qty = (sell_qty // 100) * 100
            if sell_qty > 0:
                board_break_status.sold = True
                print(f"【断板动态止盈】{symbol} 卖出{sell_qty}股")
                return sell_qty

    return None