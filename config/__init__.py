# config/__init__.py
# -*- coding: utf-8 -*-
"""
聚合所有配置子模块。
不再导出旧常量，仅提供配置对象。
"""
from .mail import *
from .account import *
from .calendar import *
from .strategy.config_objects import (
    load_strategy_config,
    StrategyConfig,
    Condition2Config,
    Condition9Config,
    Condition8Config,
    MaTradingConfig,
    PyramidProfitConfig,
    CallbackAddConfig,
)