# service/condition_service.py
# -*- coding: utf-8 -*-
"""
所有编号条件检查入口，移除向后兼容别名。
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
from config.strategy.config_objects import Condition2Config, Condition9Config

from service.conditions.cond2 import check_condition2 as check_condition2
from service.conditions.cond4 import check_condition4
from service.conditions.cond5 import check_condition5
from service.conditions.cond6 import check_condition6
from service.conditions.cond7 import check_condition7
from service.conditions.cond8 import check_condition8
from service.conditions.cond9 import check_condition9
from service.conditions.pyramid_profit import check_pyramid_profit

__all__ = [
    'check_condition2',
    'check_condition4',
    'check_condition5',
    'check_condition6',
    'check_condition7',
    'check_condition8',
    'check_condition9',
    'check_pyramid_profit',
]