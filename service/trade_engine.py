# service/trade_engine.py
# -*- coding: utf-8 -*-
"""
交易条件执行引擎 - 最终版，不再依赖 config.strategy 旧常量。
"""
from __future__ import annotations
import logging
import os
from datetime import datetime
from domain.day_data import DayData
from domain.contexts.tick_context import TickContext
from domain.decisions import DecisionArbiter, Decision
from service.order_executor import place_sell, place_buy

logger = logging.getLogger(__name__)

# 最大总卖出次数（可后续移入配置对象）
MAX_TOTAL_SELL_TIMES: int = int(os.getenv('MAX_TOTAL_SELL_TIMES', '100'))


def _execute_decision(decision: Decision,
                      order_repo,
                      condition_trigger_repo,
                      session_registry,
                      context_store,
                      ctx: TickContext):
    if decision.decision_type == 'sell':
        place_sell(decision.symbol, decision.price, decision.quantity,
                   decision.reason, decision.condition_name,
                   decision.extra.get('trigger_data', {}),
                   order_ledger=order_repo,
                   session_registry=session_registry,
                   context_store=context_store)
    elif decision.decision_type == 'buy':
        place_buy(decision.symbol, decision.price, decision.quantity,
                  decision.reason, decision.condition_name,
                  decision.extra.get('trigger_data', {}),
                  order_ledger=order_repo,
                  session_registry=session_registry,
                  context_store=context_store)
    decision.apply(ctx)


def _collect_shared_state(conditions, side_effects, context_store, symbol: str) -> dict:
    state = {}
    for cond_list in (conditions, side_effects):
        for cond in cond_list:
            if cond.condition_name == 'condition2':
                try:
                    context2 = context_store.get('condition2', symbol)
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

    # 解构所有需要的依赖
    session_registry = ctx.session_registry
    board_repo = ctx.board_repo
    order_repo = ctx.order_repo
    condition_trigger_repo = ctx.condition_trigger_repo
    cancel_lock_manager = ctx.cancel_lock_manager
    sleep_state_manager = ctx.sleep_state_manager
    condition8_tracker = ctx.condition8_tracker
    context_store = ctx.context_store
    conditions = ctx.conditions
    side_effects = ctx.side_effects

    total_sell = session_registry.get_total_sell_times(symbol)
    if total_sell >= MAX_TOTAL_SELL_TIMES:
        return

    ctx.tick_time = tick_time

    # 执行副作用条件
    for cond in side_effects:
        cond.evaluate(symbol, current_price, available_position, day_data, base_price, ctx, {})

    shared_state = _collect_shared_state(conditions, side_effects, context_store, symbol)

    arbiter = DecisionArbiter(conditions)
    best = arbiter.best_decision(symbol, current_price, available_position,
                                 day_data, base_price, ctx, shared_state)

    if best:
        try:
            _execute_decision(best, order_repo, condition_trigger_repo, session_registry, context_store, ctx)
        except Exception as e:
            logger.exception("执行决策失败 %s: %s", best.condition_name, e)