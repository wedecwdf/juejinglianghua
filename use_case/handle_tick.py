# use_case/handle_tick.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单 tick 完整流程编排——仅负责流程调度，不混杂数据操作细节。
"""

from __future__ import annotations
import logging
from typing import Dict, Any

import pytz

from domain.contexts.tick_context import TickContext
from use_case.health_check import is_in_trading_hours
from service.tick_processing_service import prepare_tick_environment
from service.tick_data_service import print_tick_snapshot
from service.trade_engine import execute_conditions
from adapter.gm_adapter import get_available_position

beijing_tz = pytz.timezone("Asia/Shanghai")
logger = logging.getLogger(__name__)


def handle_tick(tick: Dict[str, Any], ctx: TickContext) -> None:
    symbol = tick["symbol"]
    tick_time = tick["created_at"].astimezone(beijing_tz)
    if not is_in_trading_hours(tick_time):
        return

    if ctx.cancel_lock_manager.is_cancelling(symbol):
        logger.info("【撤单保护】%s 正在撤单中，跳过本次 tick 处理", symbol)
        return

    # 1. 准备环境（更新行情，处理撤单后状态）
    day_data = prepare_tick_environment(symbol, tick, ctx)

    # 2. 获取可用持仓与基准价
    current_price = tick["price"]
    available_position = get_available_position(symbol)
    base_price = day_data.base_price

    # 3. 打印快照（记录状态）
    print_tick_snapshot(
        symbol, current_price, day_data,
        ctx.session_registry, ctx.context_store,
        ctx.condition8_config
    )

    # 4. 执行交易条件
    execute_conditions(
        symbol, current_price, tick_time, available_position,
        day_data, base_price, ctx
    )

    # 5. 持久化
    ctx.order_repo.save()
    ctx.condition_trigger_repo.save()
    ctx.board_repo.save()
    ctx.callback_store.save()
    ctx.session_registry.save()