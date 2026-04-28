# service/trade_engine.py
# -*- coding: utf-8 -*-
"""
交易条件执行引擎 - 最终版，基于条件属性的插件管道。
"""
from __future__ import annotations
import logging
from datetime import datetime
from domain.day_data import DayData
from domain.contexts.tick_context import TickContext
from domain.decisions import DecisionArbiter, Decision
from config.strategy import MAX_TOTAL_SELL_TIMES
from service.order_executor import place_sell, place_buy

logger = logging.getLogger(__name__)


def _collect_shared_state(ctx: TickContext, symbol: str) -> dict:
    """收集所有条件声明依赖的状态，避免条件间直接访问上下文"""
    state = {}
    # 例如：如果条件2被启用，获取其活跃状态供其他条件使用
    for cond in ctx.conditions + ctx.side_effects:
        if cond.condition_name == 'condition2':
            context2 = ctx.context_store.get('condition2', symbol)
            state['condition2_active'] = context2.dynamic_profit_triggered
            break
    return state


def _execute_decision(decision: Decision, ctx: TickContext):
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

    ctx.tick_time = tick_time

    # 先执行副作用条件（如板数计数）
    for cond in ctx.side_effects:
        cond.evaluate(symbol, current_price, available_position, day_data, base_price, ctx, {})

    # 收集共享状态
    shared_state = _collect_shared_state(ctx, symbol)

    # 构建仲裁器并获取最佳决策
    arbiter = DecisionArbiter(ctx.conditions)
    best = arbiter.best_decision(symbol, current_price, available_position,
                                 day_data, base_price, ctx, shared_state)

    if best:
        try:
            _execute_decision(best, ctx)
        except Exception as e:
            logger.exception("执行决策失败 %s: %s", best.condition_name, e)