# config/strategy/__init__.py
# -*- coding: utf-8 -*-
"""
策略参数统一入口。技术指标参数请使用 StrategyConfig 中的 tech_indicator 字段。
"""

from .config_objects import (
    load_strategy_config,
    StrategyConfig,
    TechIndicatorConfig,
    Condition2Config,
    Condition9Config,
    Condition8Config,
    MaTradingConfig,
    PyramidProfitConfig,
    CallbackAddConfig,
    BoardConfig,
    EntryConfig,
)

# 为兼容性保留常量引用（但不再推荐直接使用）
from .indicators import *   # 空文件，无实际导出

__all__ = [
    'load_strategy_config',
    'StrategyConfig',
    'TechIndicatorConfig',
    'Condition2Config',
    'Condition9Config',
    'Condition8Config',
    'MaTradingConfig',
    'PyramidProfitConfig',
    'CallbackAddConfig',
    'BoardConfig',
    'EntryConfig',
]