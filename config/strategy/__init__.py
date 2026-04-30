# config/strategy/__init__.py
# -*- coding: utf-8 -*-
"""
策略参数统一入口。
仅导出配置对象工厂和已被对象化的常量，不再包含任何副作用或验证逻辑。
"""
from .config_objects import (
    load_strategy_config,
    StrategyConfig,
    Condition2Config,
    Condition9Config,
    Condition8Config,
    MaTradingConfig,
    PyramidProfitConfig,
    CallbackAddConfig,
)

# 为向后兼容，仍导出旧模块常量，但标记为即将弃用
from .base import *
from .indicators import *
from .board import *
from .pyramid import *
from .condition2 import *
from .condition4_7 import *
from .condition8 import *
from .condition9 import *
from .pyramid_profit import *

__all__ = [
    'load_strategy_config',
    'StrategyConfig',
    'Condition2Config',
    'Condition9Config',
    'Condition8Config',
    'MaTradingConfig',
    'PyramidProfitConfig',
    'CallbackAddConfig',
]