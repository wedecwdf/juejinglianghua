# service/trade_engine.py
# -*- coding: utf-8 -*-
"""
交易条件执行引擎 - 使用决策管道（仲裁器）。
"""
from __future__ import annotations
import logging
from datetime import datetime
from domain.day_data import DayData
from domain.board import BoardBreakState
from domain.contexts.tick_context import TickContext
from domain.decisions import Decision, DecisionArbiter, DecisionType
from domain.conditions.next_day_stop_loss import NextDayStopLossCondition
from domain.conditions.condition2 import Condition2Condition
from domain.conditions.condition9 import Condition9Condition
from config.calendar import TRADING_START_TIME
from config.strategy import MAX_TOTAL_SELL_TIMES
from service.execution import (
    execute_board_mechanisms,
    execute_pyramid_strategy,
    execute_ma_trading,
    execute_condition8_grid,
)
from service.execution.pyramid_profit_executor import execute_pyramid_profit
from service.order_executor import place_sell, place_buy
from service.pyramid_service import complete_callback_task

logger = logging.getLogger(__name__)

# 构建仲裁器：按优先级顺序（次日止损 > 条件2 > 条件9）
arbiter = DecisionArbiter([
    NextDayStopLossCondition(),
    Condition2Condition(),
    Condition9Condition(),
])

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

    # 使用仲裁器获得最佳决策（次日止损、条件2、条件9）
    decision = arbiter.best_decision(symbol, current_price, available_position,
                                     day_data, base_price, ctx)
    if decision:
        if decision.decision_type == DecisionType.SELL:
            place_sell(symbol, decision.price, decision.quantity,
                       decision.reason, decision.condition_name,
                       decision.extra.get('trigger_data', {}),
                       order_ledger=ctx.order_ledger,
                       session_registry=ctx.session_registry)
            # 更新上下文状态
            if decision.condition_name == 'condition2':
                context2 = ctx.session_registry.get_condition2(symbol)
                context2.dynamic_profit_sell_times += 1
                ctx.session_registry.increment_total_sell_times(symbol, 1)
                context2.condition2_triggered_and_sold = True
                # 清理条件9
                context9 = ctx.session_registry.get_condition9(symbol, base_price)
                context9.condition9_triggered = False
                context9.condition9_high_price = -float('inf')
                context9.condition9_profit_line = -float('inf')
            elif decision.condition_name == 'condition9':
                context9 = ctx.session_registry.get_condition9(symbol, base_price)
                context9.condition9_sell_times += 1
                ctx.session_registry.increment_total_sell_times(symbol, 1)
            return  # 卖出后直接返回

    # 如果仲裁器没有决策，继续执行其余条件（板数、金字塔、MA、条件8、金字塔止盈）
    board_status = ctx.board_repo.get_board_status(symbol)
    # 板数机制（仍包含炸板动态止盈等，内部可能直接下单）
    if execute_board_mechanisms(symbol, current_price, tick_time, available_position,
                                day_data, base_price, ctx.board_repo, ctx.session_registry):
        return

    # 动态回调加仓
    execute_pyramid_strategy(symbol, current_price, available_position, day_data,
                             ctx.callback_store, ctx.session_registry)

    # MA交易
    if execute_ma_trading(symbol, current_price, day_data, available_position, tick_time,
                          ctx.session_registry):
        return

    # 条件8网格
    if execute_condition8_grid(symbol, current_price, available_position, day_data, base_price,
                               ctx.order_ledger, ctx.session_registry):
        return

    # 金字塔止盈
    if execute_pyramid_profit(symbol, current_price, available_position, day_data, ctx.session_registry):
        return