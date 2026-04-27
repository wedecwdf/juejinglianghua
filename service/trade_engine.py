# service/trade_engine.py
# -*- coding: utf-8 -*-
"""
交易条件执行引擎 - 最终版，完全声明式决策管道。
"""
from __future__ import annotations
import logging
from datetime import datetime
from domain.day_data import DayData
from domain.contexts.tick_context import TickContext
from domain.decisions import Decision, DecisionArbiter, DecisionType
from domain.conditions.next_day_stop_loss import NextDayStopLossCondition
from domain.conditions.condition2 import Condition2Condition
from domain.conditions.condition9 import Condition9Condition
from domain.conditions.board import BoardMechanismsCondition
from domain.conditions.ma import MaTradingCondition
from domain.conditions.condition8_grid import Condition8GridCondition
from domain.conditions.pyramid_profit import PyramidProfitCondition
from domain.conditions.pyramid_add import PyramidAddCondition
from config.calendar import TRADING_START_TIME
from config.strategy import MAX_TOTAL_SELL_TIMES
from service.order_executor import place_sell, place_buy
from service.pyramid_service import complete_callback_task

logger = logging.getLogger(__name__)

# 构造决策仲裁器：按优先级排列条件（列表越前优先级越高）
arbiter = DecisionArbiter([
    NextDayStopLossCondition(),
    Condition2Condition(),
    Condition9Condition(),
    BoardMechanismsCondition(),
    PyramidAddCondition(),
    MaTradingCondition(),
    Condition8GridCondition(),
    PyramidProfitCondition(),
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

    # 获取仲裁器返回的最佳决策
    decision = arbiter.best_decision(symbol, current_price, available_position,
                                     day_data, base_price, ctx)
    if decision is None:
        return

    # 统一执行决策
    if decision.decision_type == DecisionType.SELL:
        place_sell(symbol, decision.price, decision.quantity,
                   decision.reason, decision.condition_name,
                   decision.extra.get('trigger_data', {}),
                   order_ledger=ctx.order_ledger,
                   session_registry=ctx.session_registry)
    elif decision.decision_type == DecisionType.BUY:
        place_buy(symbol, decision.price, decision.quantity,
                  decision.reason, decision.condition_name,
                  decision.extra.get('trigger_data', {}),
                  order_ledger=ctx.order_ledger,
                  session_registry=ctx.session_registry)

    # 根据决策来源更新相应的上下文状态
    if decision.condition_name == 'condition2':
        context2 = ctx.session_registry.get_condition2(symbol)
        context2.dynamic_profit_sell_times += 1
        ctx.session_registry.increment_total_sell_times(symbol, 1)
        context2.condition2_triggered_and_sold = True
        context9 = ctx.session_registry.get_condition9(symbol, base_price)
        context9.condition9_triggered = False
        context9.condition9_high_price = -float('inf')
        context9.condition9_profit_line = -float('inf')
    elif decision.condition_name == 'condition9':
        context9 = ctx.session_registry.get_condition9(symbol, base_price)
        context9.condition9_sell_times += 1
        ctx.session_registry.increment_total_sell_times(symbol, 1)
    elif decision.condition_name == 'condition7':
        context47 = ctx.session_registry.get_condition4_7(symbol)
        context47.condition7_triggered = True
        ctx.session_registry.reset_total_buy(symbol)
    elif decision.condition_name in ('condition4', 'condition5', 'condition6'):
        ctx.session_registry.set_total_buy_quantity(
            symbol,
            ctx.session_registry.get_total_buy_quantity(symbol) + decision.quantity
        )
        context47 = ctx.session_registry.get_condition4_7(symbol)
        setattr(context47, f'buy_{decision.condition_name}_triggered', True)
    elif decision.condition_name == 'condition8':
        context8 = ctx.session_registry.get_condition8(symbol, base_price)
        if decision.decision_type == DecisionType.SELL:
            context8.condition8_total_sell_today += decision.quantity
        else:
            context8.condition8_total_buy_today += decision.quantity
        context8.condition8_trade_times += 1
        context8.condition8_last_trade_price = decision.price
        context8.condition8_last_trigger_price = decision.price
    elif decision.condition_name == 'pyramid_profit':
        context = ctx.session_registry.get_pyramid(symbol, base_price)
        trigger_data = decision.extra.get('trigger_data', {})
        level = trigger_data.get('pyramid_level', 0)
        context.pyramid_profit_status[level] = True
        context.pyramid_profit_triggered = True
    elif decision.condition_name == 'callback_addition':
        complete_callback_task(symbol, store=ctx.callback_store)