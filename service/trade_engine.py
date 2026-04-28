# service/trade_engine.py
# -*- coding: utf-8 -*-
"""
交易条件执行引擎 - 最终版，完整注入 ContextStore。
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


def _execute_decision(decision: Decision, ctx: TickContext):
    if decision.decision_type == 'sell':
        place_sell(decision.symbol, decision.price, decision.quantity,
                   decision.reason, decision.condition_name,
                   decision.extra.get('trigger_data', {}),
                   order_ledger=ctx.order_ledger,
                   session_registry=ctx.session_registry,
                   context_store=ctx.context_store)
    elif decision.decision_type == 'buy':
        place_buy(decision.symbol, decision.price, decision.quantity,
                  decision.reason, decision.condition_name,
                  decision.extra.get('trigger_data', {}),
                  order_ledger=ctx.order_ledger,
                  session_registry=ctx.session_registry,
                  context_store=ctx.context_store)
    decision.apply(ctx)


def _collect_shared_state(ctx: TickContext, symbol: str) -> dict:
    state = {}
    for cond_list in (ctx.conditions, ctx.side_effects):
        for cond in cond_list:
            if cond.condition_name == 'condition2':
                try:
                    context2 = ctx.context_store.get('condition2', symbol)
                    state['condition2_active'] = context2.dynamic_profit_triggered
                except KeyError:
                    pass
                break
    return state


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

    for cond in ctx.side_effects:
        cond.evaluate(symbol, current_price, available_position, day_data, base_price, ctx, {})

    shared_state = _collect_shared_state(ctx, symbol)

    arbiter = DecisionArbiter(ctx.conditions)
    best = arbiter.best_decision(symbol, current_price, available_position,
                                 day_data, base_price, ctx, shared_state)

    if best:
        try:
            _execute_decision(best, ctx)
        except Exception as e:
            logger.exception("执行决策失败 %s: %s", best.condition_name, e)