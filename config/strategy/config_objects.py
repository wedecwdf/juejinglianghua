# config/strategy/config_objects.py
# -*- coding: utf-8 -*-
"""
策略配置数据类，将分散的常量收敛为结构化对象。
支持从环境变量动态加载，方便单元测试与多策略实例。
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import os

# ──────────────────────────────────────
#  条件2 配置
# ──────────────────────────────────────
@dataclass(frozen=True)
class Condition2Config:
    enabled: bool = True
    dynamic_profit_enabled: bool = True
    trigger_percent: float = 0.0031
    decline_percent: float = 0.001
    sell_price_offset: float = 0.001
    max_sell_times: int = 1
    dynamic_line_threshold: float = 0.025
    sell_percent_high: float = 0.3
    sell_percent_low: float = 0.1
    next_day_adjustment_enabled: bool = True
    next_day_stop_loss_offset: float = 0.01
    next_day_max_sell_ratio: float = 0.5
    next_day_max_days: int = 10

# ──────────────────────────────────────
#  条件9 配置
# ──────────────────────────────────────
@dataclass(frozen=True)
class Condition9Config:
    enabled: bool = True
    upper_band_percent: float = 0.02
    lower_band_percent: float = 0.001
    trigger_percent: float = 0.0015
    decline_percent: float = 0.0004
    sell_price_offset: float = 0.001
    dynamic_line_threshold: float = 0.01
    sell_percent_high: float = 0.1
    sell_percent_low: float = 0.05
    max_sell_times: int = 1

# ──────────────────────────────────────
#  条件8 配置（完整，待后文迁移时使用）
# ──────────────────────────────────────
@dataclass(frozen=True)
class Condition8Config:
    enabled: bool = True
    max_trade_times: int = 100
    rise_percent: float = 0.1
    decline_percent: float = 0.1
    multiple_order_enabled: bool = True
    grid_interval_percent: float = 0.01
    max_multiple_limit: int = 10
    high_freq_rise: float = 0.12
    high_freq_decline: float = 0.12
    low_freq_rise: float = 0.011
    low_freq_decline: float = 0.011
    price_band_enabled: bool = True
    upper_band_percent: float = 0.16
    lower_band_percent: float = 0.16
    high_freq_stocks: List[str] = field(default_factory=list)
    low_freq_stocks: List[str] = field(default_factory=list)
    sell_quantity: Dict[str, int] = field(default_factory=dict)
    buy_quantity: Dict[str, int] = field(default_factory=dict)
    max_total_quantity: Dict[str, int] = field(default_factory=dict)

# ──────────────────────────────────────
#  顶层聚合配置
# ──────────────────────────────────────
@dataclass(frozen=True)
class StrategyConfig:
    condition2: Condition2Config = field(default_factory=Condition2Config)
    condition9: Condition9Config = field(default_factory=Condition9Config)
    condition8: Condition8Config = field(default_factory=Condition8Config)

# ──────────────────────────────────────
#  工厂函数：从环境变量覆盖默认值
# ──────────────────────────────────────
def load_strategy_config() -> StrategyConfig:
    c2 = Condition2Config(
        enabled=os.getenv('CONDITION2_ENABLED', 'true').lower() == 'true',
        trigger_percent=float(os.getenv('CONDITION2_TRIGGER_PERCENT', 0.0031)),
        decline_percent=float(os.getenv('CONDITION2_DECLINE_PERCENT', 0.001)),
        sell_price_offset=float(os.getenv('CONDITION2_SELL_OFFSET', 0.001)),
        max_sell_times=int(os.getenv('CONDITION2_MAX_SELL', 1)),
        dynamic_line_threshold=float(os.getenv('CONDITION2_LINE_THRESHOLD', 0.025)),
        sell_percent_high=float(os.getenv('CONDITION2_SELL_HIGH', 0.3)),
        sell_percent_low=float(os.getenv('CONDITION2_SELL_LOW', 0.1)),
    )
    c9 = Condition9Config(
        enabled=os.getenv('CONDITION9_ENABLED', 'true').lower() == 'true',
        upper_band_percent=float(os.getenv('CONDITION9_UPPER', 0.02)),
        lower_band_percent=float(os.getenv('CONDITION9_LOWER', 0.001)),
        trigger_percent=float(os.getenv('CONDITION9_TRIGGER', 0.0015)),
        decline_percent=float(os.getenv('CONDITION9_DECLINE', 0.0004)),
        sell_price_offset=float(os.getenv('CONDITION9_OFFSET', 0.001)),
    )
    # 条件8暂时使用默认值，后续迁移时启用环境变量
    c8 = Condition8Config()
    return StrategyConfig(condition2=c2, condition9=c9, condition8=c8)