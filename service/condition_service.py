# service/condition_service.py
# -*- coding: utf-8 -*-
"""
所有编号条件检查入口，config 参数不再提供默认值（由调用方传入）。
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.contexts.condition2 import Condition2Context
from domain.contexts.condition8 import Condition8Context
from domain.contexts.condition9 import Condition9Context
from domain.contexts.condition4_7 import Condition4To7Context
from domain.contexts.pyramid import PyramidContext
from domain.stores.base import AbstractOrderLedger
from config.strategy.config_objects import Condition2Config, Condition9Config, Condition8Config

from service.conditions.cond2 import check_condition2 as _cond2
from service.conditions.cond4 import check_condition4 as _cond4
from service.conditions.cond5 import check_condition5 as _cond5
from service.conditions.cond6 import check_condition6 as _cond6
from service.conditions.cond7 import check_condition7 as _cond7
from service.conditions.cond8 import check_condition8 as _cond8
from service.conditions.cond9 import check_condition9 as _cond9
from service.conditions.pyramid_profit import check_pyramid_profit as _pyramid


def check_condition2(context: Condition2Context, increase: float, current_price: float,
                     base_price: float, board_break_active: bool = False,
                     config: Condition2Config = None) -> Optional[Dict[str, Any]]:
    return _cond2(context, increase, current_price, base_price, board_break_active, config)


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
                     order_ledger: AbstractOrderLedger,
                     config: Condition8Config = None) -> Optional[Dict[str, Any]]:
    return _cond8(day_data, context, current_price, available_position, order_ledger, config)


def check_condition9(context: Condition9Context, increase: float, current_price: float,
                     base_price: float, board_break_active: bool = False,
                     condition2_active: bool = False,
                     config: Condition9Config = None) -> Optional[Dict[str, Any]]:
    return _cond9(context, increase, current_price, base_price, board_break_active, condition2_active, config)


def check_pyramid_profit(symbol: str, context: PyramidContext, current_price: float,
                         available_position: int) -> Optional[Dict[str, Any]]:
    return _pyramid(symbol, context, current_price, available_position)