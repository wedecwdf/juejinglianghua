# use_case/handle_tick.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单 tick 完整流程 - 依赖注入版
不再内部创建仓库实例。
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Dict, Any
import pytz
from repository.gm_data_source import get_available_position
from service.tick_data_service import update_day_data, refresh_indicators, print_tick_snapshot
from service.trade_engine import execute_conditions
from use_case.health_check import is_in_trading_hours
from domain.stores import SessionRegistry, BoardStateRepository, CallbackTaskStore, OrderLedger

beijing_tz = pytz.timezone("Asia/Shanghai")

def handle_tick(tick: Dict[str, Any],
                session_registry: SessionRegistry,
                board_repo: BoardStateRepository,
                callback_store: CallbackTaskStore,
                order_ledger: OrderLedger) -> None:
    symbol = tick["symbol"]
    tick_time = tick["created_at"].astimezone(beijing_tz)
    if not is_in_trading_hours(tick_time):
        return
    tick_date = tick_time.date()
    current_price = tick["price"]

    if order_ledger.is_cancelling(symbol):
        print(f"【撤单保护】{symbol} 正在撤单中，跳过本次 tick 处理")
        return

    day_data = update_day_data(symbol, tick, tick_date, session_registry)

    if day_data.condition2_post_cancel_rechecked:
        day_data.condition2_post_cancel_rechecked = False
    if day_data.condition9_post_cancel_rechecked:
        day_data.condition9_post_cancel_rechecked = False

    if order_ledger.pop_cancelled(symbol):
        print(f"【撤单再判断】{symbol} 上次撤单已清除，立即重新判断条件")

    refresh_indicators(symbol, day_data)
    available_position = get_available_position(symbol)

    base_price = day_data.base_price
    print_tick_snapshot(symbol, current_price, day_data)

    execute_conditions(symbol, current_price, tick_time, available_position,
                       day_data, base_price,
                       board_repo=board_repo,
                       callback_store=callback_store,
                       order_ledger=order_ledger,
                       session_registry=session_registry)

    # 各仓库独立保存
    order_ledger.save()
    board_repo.save()
    callback_store.save()
    session_registry.save()