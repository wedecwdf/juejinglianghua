# config/strategy/__init__.py
# -*- coding: utf-8 -*-
"""
策略参数统一入口。
提供新的配置对象（推荐使用）以及向后兼容的旧常量（即将弃用）。
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

# 向后兼容的旧常量导出（逐步将引用迁移至 config_objects）
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