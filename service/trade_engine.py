# service/trade_engine.py
# -*- coding: utf-8 -*-
"""
交易条件执行引擎 - 依赖注入版
修复循环导入：延迟导入 use_case.health_check
"""
from __future__ import annotations
from datetime import datetime
from domain.day_data import DayData
from domain.board import BoardBreakState
from domain.stores import BoardStateRepository, CallbackTaskStore, OrderLedger, SessionRegistry
from config.calendar import TRADING_START_TIME
from config.strategy import MAX_TOTAL_SELL_TIMES

# 为避免循环导入，不再从 use_case 模块顶层导入
# from use_case.health_check import should_start_trading, get_trading_start_datetime

from service.execution import (
    execute_next_day_stop_loss,
    execute_board_mechanisms,
    execute_pyramid_strategy,
    execute_condition2_profit,
    execute_condition9_profit,
    execute_ma_trading,
    execute_condition8_grid,
)
from service.execution.pyramid_profit_executor import execute_pyramid_profit
from service.dynamic_profit_recheck_service import execute_post_cancel_recheck

def execute_conditions(symbol: str, current_price: float,
                       tick_time: datetime, available_position: int,
                       day_data: DayData, base_price: float,
                       board_repo: BoardStateRepository,
                       callback_store: CallbackTaskStore,
                       order_ledger: OrderLedger,
                       session_registry: SessionRegistry) -> None:
    # 延迟导入，避免循环依赖
    from use_case.health_check import should_start_trading, get_trading_start_datetime

    if not should_start_trading(tick_time):
        if tick_time.minute % 5 == 0 and tick_time.second == 0:
            trading_start = get_trading_start_datetime(tick_time)
            if trading_start:
                remaining = (trading_start - tick_time).total_seconds()
                if remaining > 0:
                    minutes, seconds = divmod(int(remaining), 60)
                    hours, minutes = divmod(minutes, 60)
                    print(f"【等待交易开始】{symbol} {tick_time.strftime('%H:%M:%S')} "
                          f"距离交易开始{TRADING_START_TIME}还有{hours}小时{minutes}分")
        return

    if day_data.total_sell_times >= MAX_TOTAL_SELL_TIMES:
        return

    # Layer 1
    if execute_next_day_stop_loss(symbol, current_price, available_position, day_data, session_registry):
        return

    # Layer 2
    board_status = board_repo.get_board_status(symbol)
    board_break_active = board_status.get_break_state() in (BoardBreakState.STAGE1_MONITORING, BoardBreakState.STAGE2_TAKEOVER)

    if execute_board_mechanisms(symbol, current_price, tick_time, available_position,
                                day_data, base_price, board_repo, session_registry):
        return

    # Layer 3
    execute_pyramid_strategy(symbol, current_price, available_position, day_data, callback_store, session_registry)

    # 撤单重新判定
    if day_data.condition2_recheck_after_cancel or day_data.condition9_recheck_after_cancel:
        print(f"【重新判定触发】{symbol} 检测到动态止盈撤单后重新判定标记，优先执行重新判定")
        execute_post_cancel_recheck(symbol, current_price, available_position, day_data, base_price, board_break_active)

    # Layer 4
    if not day_data.condition2_post_cancel_rechecked:
        if execute_condition2_profit(symbol, current_price, available_position, day_data, base_price, board_break_active, session_registry):
            return
    else:
        print(f"【条件2常规跳过】{symbol} 本次tick已进行撤单后重新判定，跳过常规条件2检查")

    # Layer 5
    if not day_data.condition9_post_cancel_rechecked:
        if execute_condition9_profit(symbol, current_price, available_position, day_data, base_price, board_break_active,
                                     day_data.dynamic_profit_triggered, session_registry):
            return
    else:
        print(f"【条件9常规跳过】{symbol} 本次tick已进行撤单后重新判定，跳过常规条件9检查")

    # Layer 6
    if execute_ma_trading(symbol, current_price, day_data, available_position, tick_time, session_registry):
        return

    # Layer 7
    if execute_condition8_grid(symbol, current_price, available_position, day_data, base_price, order_ledger, session_registry):
        return

    # Layer 8
    if execute_pyramid_profit(symbol, current_price, available_position, day_data, session_registry):
        return