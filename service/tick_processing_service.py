# service/tick_processing_service.py
# -*- coding: utf-8 -*-
"""
tick 处理流程中可抽离的纯逻辑服务函数，无副作用，可独立测试。
"""

from __future__ import annotations
import logging
from typing import Dict, Any

from domain.day_data import DayData
from domain.contexts.tick_context import TickContext
from service.tick_data_service import refresh_indicators as do_refresh_indicators

logger = logging.getLogger(__name__)


def reset_post_cancel_flags(ctx: TickContext, symbol: str) -> None:
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


def handle_post_cancel_refresh(ctx: TickContext, symbol: str, day_data: DayData) -> None:
    if ctx.cancel_lock_manager.pop_cancelled(symbol):
        logger.info("【撤单再判断】%s 上次撤单已清除，立即重新判断条件", symbol)
        do_refresh_indicators(symbol, day_data, ctx.tech_indicator_config)


def prepare_tick_environment(symbol: str, tick: Dict[str, Any],
                             ctx: TickContext) -> DayData:
    from .tick_data_service import update_day_data as do_update
    tick_date = tick["created_at"].astimezone().date()
    day_data = do_update(symbol, tick, tick_date, ctx.session_registry)
    reset_post_cancel_flags(ctx, symbol)
    handle_post_cancel_refresh(ctx, symbol, day_data)
    return day_data