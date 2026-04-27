# use_case/handle_tick.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单 tick 完整流程 - 依赖注入版，使用正式上下文属性。
"""
from __future__ import annotations
import logging
from datetime import date, datetime
from typing import Dict, Any
import pytz
from repository.gm_data_source import get_available_position
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

    if ctx.order_ledger.is_cancelling(symbol):
        logger.info("【撤单保护】%s 正在撤单中，跳过本次 tick 处理", symbol)
        return

    # 更新 DayData（仅行情）
    day_data = update_day_data(symbol, tick, tick_date, ctx.session_registry)

    # 防重复标记清理
    context2 = ctx.session_registry.get_condition2(symbol)
    context9 = ctx.session_registry.get_condition9(symbol, day_data.base_price)
    if context2.post_cancel_rechecked:
        context2.post_cancel_rechecked = False
    if context9.post_cancel_rechecked:
        context9.post_cancel_rechecked = False

    # 撤单后重新判断标记
    if ctx.order_ledger.pop_cancelled(symbol):
        logger.info("【撤单再判断】%s 上次撤单已清除，立即重新判断条件", symbol)

    # 指标刷新
    refresh_indicators(symbol, day_data)
    available_position = get_available_position(symbol)

    base_price = day_data.base_price
    print_tick_snapshot(symbol, current_price, day_data, ctx.session_registry)

    # 执行交易条件
    execute_conditions(symbol, current_price, tick_time, available_position,
                       day_data, base_price, ctx)

    # 各仓库独立保存
    ctx.order_ledger.save()
    ctx.board_repo.save()
    ctx.callback_store.save()
    ctx.session_registry.save()