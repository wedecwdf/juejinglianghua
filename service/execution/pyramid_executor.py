# service/execution/pyramid_executor.py
# -*- coding: utf-8 -*-
"""
动态回调加仓执行器（Layer 3）
"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.stores import CallbackTaskStore, SessionRegistry
from service.pyramid_service import check_callback_strategy, complete_callback_task
from service.order_executor import place_buy
from config.strategy import CALLBACK_ADDITION_ENABLED

logger = logging.getLogger(__name__)

def execute_pyramid_strategy(symbol: str, current_price: float,
                             available_position: int, day_data: DayData,
                             store: CallbackTaskStore,
                             session_registry: SessionRegistry) -> None:
    if not CALLBACK_ADDITION_ENABLED:
        return
    result = check_callback_strategy(symbol, current_price, store=store)
    if result:
        buy_price = current_price
        quantity = result['quantity']
        reason = result['reason']
        condition_type = 'callback_addition'
        place_buy(symbol, buy_price, quantity, reason, condition_type, result.get('trigger_data', {}),
                  session_registry=session_registry)
        complete_callback_task(symbol, store=store)
        logger.info("【动态回调加仓执行】%s 买入委托已发送: 数量=%d股, 价格=%.4f, 原因=%s",
                    symbol, quantity, buy_price, reason)