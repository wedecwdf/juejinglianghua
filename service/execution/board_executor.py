# service/execution/board_executor.py
# -*- coding: utf-8 -*-
"""
板数、炸板动态止盈、断板机制执行器（Layer 2）
修改：传入 session_registry 到 handle_dynamic_profit_on_board_break。
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Optional
from domain.day_data import DayData
from domain.board import BoardStatus
from domain.stores import BoardStateRepository, SessionRegistry
from service.board_service import (
    handle_board_counting,
    handle_board_break_mechanism,
    handle_dynamic_profit_on_board_break
)
from service.order_executor import place_sell
from config.strategy import BOARD_BREAK_DYNAMIC_PROFIT_PRICE_OFFSET, BOARD_BREAK_PRICE_OFFSET

def _fix_board_status_datetime(board_status: BoardStatus) -> None:
    time_fields = ['sealed_start_time', 'opened_start_time',
                   'board_break_start_time', 'last_limit_up_time']
    for field in time_fields:
        val = getattr(board_status, field, None)
        if isinstance(val, str):
            try:
                setattr(board_status, field, datetime.fromisoformat(val))
            except Exception:
                setattr(board_status, field, None)
    date_fields = ['last_effective_sealed_date', 'first_board_date']
    for field in date_fields:
        val = getattr(board_status, field, None)
        if isinstance(val, str):
            try:
                setattr(board_status, field, date.fromisoformat(val))
            except Exception:
                setattr(board_status, field, None)

def execute_board_mechanisms(symbol: str, current_price: float, tick_time: datetime,
                             available_position: int, day_data: DayData,
                             prev_close: float,
                             board_repo: BoardStateRepository,
                             session_registry: SessionRegistry) -> bool:
    board_status = board_repo.get_board_status(symbol)
    _fix_board_status_datetime(board_status)
    board_count_data = board_repo.get_board_count_data(symbol)
    board_break_status = board_repo.get_board_break_status(symbol)

    board_count_data = handle_board_counting(symbol, current_price, prev_close, tick_time,
                                             board_status, board_count_data)
    if board_count_data is None:
        board_repo.set_board_count_data(symbol, None)
    else:
        board_repo.set_board_count_data(symbol, board_count_data)

    sell_qty = handle_dynamic_profit_on_board_break(symbol, current_price, available_position,
                                                    day_data, board_status, session_registry)
    if sell_qty:
        place_sell(symbol, current_price - BOARD_BREAK_DYNAMIC_PROFIT_PRICE_OFFSET, sell_qty,
                   "炸板动态止盈卖出", "board_dynamic_profit", {},
                   session_registry=session_registry)
        return True

    sell_qty = handle_board_break_mechanism(symbol, current_price, prev_close, tick_time,
                                            board_status, board_break_status, available_position)
    if sell_qty:
        place_sell(symbol, current_price - BOARD_BREAK_PRICE_OFFSET, sell_qty,
                   "断板卖出", "board_break", {},
                   session_registry=session_registry)
        board_break_status.sold = True
        return True
    return False