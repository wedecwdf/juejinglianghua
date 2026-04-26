# service/conditions/cond8.py
# -*- coding: utf-8 -*-
"""
条件8：动态基准价交易（含倍数委托、高频/低频独立阈值、休眠机制、防重复机制）
修改：从 domain.stores 统一导入 OrderLedger
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.stores import OrderLedger
from .cond8_validation import _check_system_state, _validate_business_rules, _fetch_data
from .cond8_execution import _execute_trading_logic

def check_condition8(day_data: DayData, current_price: float,
                     available_position: int,
                     order_ledger: Optional[OrderLedger] = None) -> Optional[Dict[str, Any]]:
    if order_ledger is None:
        order_ledger = OrderLedger()

    if not _check_system_state(order_ledger, day_data, current_price):
        return None

    if not _validate_business_rules(day_data, current_price):
        return None

    data_context = _fetch_data(order_ledger, day_data, current_price)

    return _execute_trading_logic(
        day_data=day_data,
        current_price=current_price,
        available_position=available_position,
        ref_price=data_context["ref_price"],
        price_change=(current_price - data_context["ref_price"]) / data_context["ref_price"],
        rise_threshold=data_context["rise_threshold"],
        decline_threshold=data_context["decline_threshold"],
        stock_type=data_context["stock_type"],
        type_desc=data_context["type_desc"]
    )