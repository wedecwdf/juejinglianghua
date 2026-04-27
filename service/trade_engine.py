# service/trade_engine.py
# -*- coding: utf-8 -*-
"""
交易条件执行引擎 - 最终版，使用 logger。
"""
from __future__ import annotations
import logging
from datetime import datetime
from domain.day_data import DayData
from domain.board import BoardBreakState
from domain.contexts.tick_context import TickContext
from config.calendar import TRADING_START_TIME
from config.strategy import MAX_TOTAL_SELL_TIMES
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

logger = logging.getLogger(__name__)

def execute_conditions(symbol: str, current_price: float,
                       tick_time: datetime, available_position: int,
                       day_data: DayData, base_price: float,
                       ctx: TickContext) -> None:
    from use_case.health_check import should_start_trading, get_trading_start_datetime

    if not should_start_trading(tick_time):
        if tick_time.minute % 5 == 0 and tick_time.second == 0:
            trading_start = get_trading_start_datetime(tick_time)
            if trading_start:
                remaining = (trading_start - tick_time).total_seconds()
                if remaining > 0:
                    minutes, seconds = divmod(int(remaining), 60)
                    hours, minutes = divmod(minutes, 60)
                    logger.info("【等待交易开始】%s %s 距离交易开始%s还有%d小时%d分",
                                symbol, tick_time.strftime('%H:%M:%S'),
                                TRADING_START_TIME, hours, minutes)
        return

    total_sell = ctx.session_registry.get_total_sell_times(symbol)
    if total_sell >= MAX_TOTAL_SELL_TIMES:
        return

    # Layer 1
    if execute_next_day_stop_loss(symbol, current_price, available_position, day_data, ctx.session_registry):
        return

    # Layer 2
    board_status = ctx.board_repo.get_board_status(symbol)
    board_break_active = board_status.get_break_state() in (BoardBreakState.STAGE1_MONITORING, BoardBreakState.STAGE2_TAKEOVER)

    if execute_board_mechanisms(symbol, current_price, tick_time, available_position,
                                day_data, base_price, ctx.board_repo, ctx.session_registry):
        return

    # Layer 3
    execute_pyramid_strategy(symbol, current_price, available_position, day_data, ctx.callback_store, ctx.session_registry)

    # 撤单重新判定
    context2 = ctx.session_registry.get_condition2(symbol)
    context9 = ctx.session_registry.get_condition9(symbol, base_price)
    if getattr(context2, '_recheck_after_cancel', False) or getattr(context9, '_recheck_after_cancel', False):
        logger.info("【重新判定触发】%s 检测到动态止盈撤单后重新判定标记", symbol)
        execute_post_cancel_recheck(symbol, current_price, available_position, day_data, base_price,
                                    board_break_active, ctx.session_registry)

    # Layer 4
    if not getattr(context2, '_post_cancel_rechecked', False):
        if execute_condition2_profit(symbol, current_price, available_position, day_data, base_price,
                                     board_break_active, ctx.session_registry, ctx.config.condition2):
            return
    else:
        logger.info("【条件2常规跳过】%s 本次tick已进行撤单后重新判定，跳过常规条件2检查", symbol)

    # Layer 5
    if not getattr(context9, '_post_cancel_rechecked', False):
        if execute_condition9_profit(symbol, current_price, available_position, day_data, base_price,
                                     board_break_active, context2.dynamic_profit_triggered,
                                     ctx.session_registry, ctx.config.condition9):
            return
    else:
        logger.info("【条件9常规跳过】%s 本次tick已进行撤单后重新判定，跳过常规条件9检查", symbol)

    # Layer 6
    if execute_ma_trading(symbol, current_price, day_data, available_position, tick_time, ctx.session_registry):
        return

    # Layer 7
    if execute_condition8_grid(symbol, current_price, available_position, day_data, base_price,
                               ctx.order_ledger, ctx.session_registry):
        return

    # Layer 8
    if execute_pyramid_profit(symbol, current_price, available_position, day_data, ctx.session_registry):
        return