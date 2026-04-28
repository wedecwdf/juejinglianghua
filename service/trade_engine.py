# service/trade_engine.py
# -*- coding: utf-8 -*-
"""
交易条件执行引擎 - 最终版，动态管道 + 自更新决策 + 板数副作用。
"""
from __future__ import annotations
import logging
from datetime import datetime
from domain.day_data import DayData
from domain.contexts.tick_context import TickContext
from domain.decisions import DecisionArbiter, Decision
from domain.conditions.registry import ConditionRegistry
from domain.conditions.board import BoardCountingCondition
from config.calendar import TRADING_START_TIME
from config.strategy import MAX_TOTAL_SELL_TIMES
from service.order_executor import place_sell, place_buy

logger = logging.getLogger(__name__)


def _execute_decision(decision: Decision, ctx: TickContext):
    """统一执行决策：下单 + 状态更新"""
    if decision.decision_type == 'sell':
        place_sell(decision.symbol, decision.price, decision.quantity,
                   decision.reason, decision.condition_name,
                   decision.extra.get('trigger_data', {}),
                   order_ledger=ctx.order_ledger,
                   session_registry=ctx.session_registry)
    elif decision.decision_type == 'buy':
        place_buy(decision.symbol, decision.price, decision.quantity,
                  decision.reason, decision.condition_name,
                  decision.extra.get('trigger_data', {}),
                  order_ledger=ctx.order_ledger,
                  session_registry=ctx.session_registry)
    decision.apply(ctx)


def execute_conditions(symbol: str, current_price: float,
                       tick_time: datetime, available_position: int,
                       day_data: DayData, base_price: float,
                       ctx: TickContext) -> None:
    from use_case.health_check import should_start_trading

    if not should_start_trading(tick_time):
        return

    total_sell = ctx.session_registry.get_total_sell_times(symbol)
    if total_sell >= MAX_TOTAL_SELL_TIMES:
        return

    # 获取所有已注册条件
    all_conditions = ConditionRegistry.get_conditions()

    # 分离副作用条件（板数计数）和决策条件
    side_effect_conditions = [c for c in all_conditions if isinstance(c, BoardCountingCondition)]
    decision_conditions = [c for c in all_conditions if not isinstance(c, BoardCountingCondition)]

    # 先执行副作用条件（封板计数、状态机更新）
    for cond in side_effect_conditions:
        cond.evaluate(symbol, current_price, available_position, day_data, base_price, ctx)

    # 构建仲裁器（只包含可产生决策的条件）
    arbiter = DecisionArbiter(decision_conditions)
    best = arbiter.best_decision(symbol, current_price, available_position,
                                 day_data, base_price, ctx)

    if best:
        try:
            _execute_decision(best, ctx)
        except Exception as e:
            logger.exception("执行决策失败 %s: %s", best.condition_name, e)