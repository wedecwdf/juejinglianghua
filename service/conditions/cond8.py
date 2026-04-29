# service/conditions/cond8.py
# -*- coding: utf-8 -*-
"""
条件8：动态基准价交易（主入口）。
增加 config 参数，实现配置注入。
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.contexts.condition8 import Condition8Context
from domain.stores.base import AbstractOrderLedger
from config.strategy.config_objects import Condition8Config, load_strategy_config
from .cond8_validation import _check_system_state, _validate_business_rules, _fetch_data
from .cond8_execution import _execute_trading_logic

def check_condition8(day_data: DayData, context: Condition8Context, current_price: float,
                     available_position: int,
                     order_ledger: AbstractOrderLedger,
                     config: Optional[Condition8Config] = None) -> Optional[Dict[str, Any]]:
    if config is None:
        config = load_strategy_config().condition8   # 向后兼容

    symbol = day_data.symbol
    if not _check_system_state(order_ledger, symbol, context, current_price, config):
        return None
    if not _validate_business_rules(context, day_data.base_price, current_price, config):
        return None

    data_context = _fetch_data(order_ledger, symbol, context, current_price, config)
    ref_price = data_context["ref_price"]
    price_change = (current_price - ref_price) / ref_price if ref_price else 0.0

    return _execute_trading_logic(
        day_data=day_data,
        context=context,
        current_price=current_price,
        available_position=available_position,
        ref_price=ref_price,
        price_change=price_change,
        rise_threshold=data_context["rise_threshold"],
        decline_threshold=data_context["decline_threshold"],
        stock_type=data_context["stock_type"],
        type_desc=data_context["type_desc"],
        config=config,
    )