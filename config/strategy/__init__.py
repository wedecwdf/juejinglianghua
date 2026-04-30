# config/strategy/__init__.py
# -*- coding: utf-8 -*-
"""
策略参数统一入口。
提供配置对象和纯技术指标常量。
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
from .indicators import *   # 导出技术指标参数（仅此一处旧常量保留）

__all__ = [
    'load_strategy_config',
    'StrategyConfig',
    'Condition2Config',
    'Condition9Config',
    'Condition8Config',
    'MaTradingConfig',
    'PyramidProfitConfig',
    'CallbackAddConfig',
    'MA_PERIODS', 'CCI_PERIOD', 'MACD_FAST', 'MACD_SLOW', 'MACD_SIGNAL',
    'MACD_MIN_PERIOD', 'CCI_UPPER_LIMIT', 'CCI_LOWER_LIMIT',
    'VOLUME_BAR_COUNT', 'MACD_HIST_BAR_COUNT', 'MAX_HISTORY_DAYS',
]