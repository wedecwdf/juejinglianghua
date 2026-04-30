# config/__init__.py
# -*- coding: utf-8 -*-
"""
聚合所有配置子模块。
同时导出配置对象和必要的公共接口。
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
# 向后兼容的旧常量导出
from .strategy import *