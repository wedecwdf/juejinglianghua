# service/condition_service.py
# -*- coding: utf-8 -*-
"""
所有编号条件检查入口，保持对外接口兼容。
修改：增加上下文参数并委托给新实现。
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.contexts.condition2 import Condition2Context
from domain.contexts.condition8 import Condition8Context
from domain.contexts.condition9 import Condition9Context
from domain.contexts.condition4_7 import Condition4To7Context
from domain.contexts.pyramid import PyramidContext
from domain.stores import OrderLedger

from service.conditions import (
    check_condition2 as _cond2,
    check_condition4 as _cond4,
    check_condition5 as _cond5,
    check_condition6 as _cond6,
    check_condition7 as _cond7,
    check_condition8 as _cond8,
    check_condition9 as _cond9,
    check_pyramid_profit as _pyramid,
)

def check_condition2(day_data: DayData, increase: float, current_price: float,
                     base_price: float, context: Condition2Context,
                     board_break_active: bool = False) -> Optional[Dict[str, Any]]:
    return _cond2(context, increase, current_price, base_price, board_break_active)

def check_condition4(day_data: DayData, context: Condition4To7Context,
                     current_price: float) -> Optional[Dict[str, Any]]:
    return _cond4(day_data, context, current_price)

def check_condition5(day_data: DayData, context: Condition4To7Context,
                     current_price: float) -> Optional[Dict[str, Any]]:
    return _cond5(day_data, context, current_price)

def check_condition6(day_data: DayData, context: Condition4To7Context,
                     current_price: float) -> Optional[Dict[str, Any]]:
    return _cond6(day_data, context, current_price)

def check_condition7(day_data: DayData, context: Condition4To7Context,
                     current_price: float, tick_time) -> Optional[Dict[str, Any]]:
    return _cond7(day_data, context, current_price, tick_time)

def check_condition8(day_data: DayData, context: Condition8Context, current_price: float,
                     available_position: int,
                     order_ledger: Optional[OrderLedger] = None) -> Optional[Dict[str, Any]]:
    return _cond8(day_data, context, current_price, available_position, order_ledger)

def check_condition9(day_data: DayData, increase: float, current_price: float,
                     base_price: float, context: Condition9Context,
                     board_break_active: bool = False,
                     condition2_active: bool = False) -> Optional[Dict[str, Any]]:
    return _cond9(context, increase, current_price, base_price, board_break_active, condition2_active)

def check_pyramid_profit(symbol: str, context: PyramidContext, current_price: float,
                         available_position: int) -> Optional[Dict[str, Any]]:
    return _pyramid(symbol, context, current_price, available_position)