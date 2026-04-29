# use_case/handle_tick.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单 tick 完整流程 - 使用拆分后的小接口，消除上帝对象。
"""
from __future__ import annotations
import logging
from datetime import date, datetime
from typing import Dict, Any
import pytz
from service.tick_data_service import update_day_data, refresh_indicators, print_tick_snapshot
from service.trade_engine import execute_conditions
from use_case.health_check import is_in_trading_hours
from domain.contexts.tick_context import TickContext

beijing_tz = pytz.timezone("Asia/Shanghai")
logger = logging.getLogger(__name__)

def handle_tick(tick: Dict[str, Any], ctx: TickContext) -> None:
    symbol = tick["symbol"]
    tick_time = tick["created_at"].astimezone(beijing_tz)
    if not is_in_trading_hours(tick_time):
        return
    tick_date = tick_time.date()
    current_price = tick["price"]

    # 使用拆分后的小接口
    if ctx.cancel_lock_manager.is_cancelling(symbol):
        logger.info("【撤单保护】%s 正在撤单中，跳过本次 tick 处理", symbol)
        return

    # 更新 DayData（仅行情）
    day_data = update_day_data(symbol, tick, tick_date, ctx.session_registry)

    # 防重复标记清理
    try:
        context2 = ctx.context_store.get('condition2', symbol)
        if context2.post_cancel_rechecked:
            context2.post_cancel_rechecked = False
    except KeyError:
        pass

    try:
        context9 = ctx.context_store.get('condition9', symbol)
        if context9 and context9.post_cancel_rechecked:
            context9.post_cancel_rechecked = False
    except KeyError:
        pass

    # 撤单后重新判断标记（通过 cancel_lock_manager 操作）
    if ctx.cancel_lock_manager.pop_cancelled(symbol):
        logger.info("【撤单再判断】%s 上次撤单已清除，立即重新判断条件", symbol)

    # 指标刷新
    refresh_indicators(symbol, day_data)

    # 可用持仓
    from adapter.gm_adapter import get_available_position
    available_position = get_available_position(symbol)

    base_price = day_data.base_price
    print_tick_snapshot(symbol, current_price, day_data, ctx.session_registry, ctx.context_store)

    # 执行交易条件（内部已解构 ctx）
    execute_conditions(symbol, current_price, tick_time, available_position,
                       day_data, base_price, ctx)

    # 持久化保存（使用拆分接口）
    ctx.order_repo.save()
    ctx.condition_trigger_repo.save()
    ctx.board_repo.save()
    ctx.callback_store.save()
    ctx.session_registry.save()