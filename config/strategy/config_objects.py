# config/strategy/config_objects.py
# -*- coding: utf-8 -*-
"""
策略配置数据类，将分散的常量收敛为结构化对象。
支持从环境变量动态覆盖默认值。
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
#  条件8 完整配置
# ──────────────────────────────────────
@dataclass(frozen=True)
class Condition8Config:
    enabled: bool = True
    max_trade_times: int = 100
    rise_percent: float = 0.1         # 默认上涨触发百分比
    decline_percent: float = 0.1      # 默认下跌触发百分比
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
#  MA / 条件4-7 配置
# ──────────────────────────────────────
@dataclass(frozen=True)
class MaTradingConfig:
    condition4_enabled: bool = False
    condition5_enabled: bool = False
    condition6_enabled: bool = False
    condition7_enabled: bool = False
    buy_below_ma4_qty: int = 100
    buy_below_ma8_qty: int = 100
    buy_below_ma12_qty: int = 100

# ──────────────────────────────────────
#  金字塔止盈配置
# ──────────────────────────────────────
@dataclass(frozen=True)
class PyramidProfitConfig:
    enabled: bool = True
    user_base_price: Dict[str, float] = field(default_factory=dict)
    total_quantity: Dict[str, int] = field(default_factory=dict)
    sell_price_offset: float = 0.01
    # 分级止盈参数
    high_freq_levels: List[float] = field(default_factory=lambda: [0.035, 0.045, 0.065])
    high_freq_ratios: List[float] = field(default_factory=lambda: [0.2, 0.3, 0.5])
    low_freq_levels: List[float] = field(default_factory=lambda: [0.05, 0.07, 0.1])
    low_freq_ratios: List[float] = field(default_factory=lambda: [0.1, 0.2, 0.7])
    default_levels: List[float] = field(default_factory=lambda: [0.02, 0.03, 0.039])
    default_ratios: List[float] = field(default_factory=lambda: [0.1, 0.1, 0.1])

# ──────────────────────────────────────
#  动态回调加仓配置
# ──────────────────────────────────────
@dataclass(frozen=True)
class CallbackAddConfig:
    enabled: bool = True
    min_trade_unit: int = 100
    on_condition2: bool = True
    on_condition9: bool = True
    on_condition8: bool = True
    buy_price_offset: float = 0.01

# ──────────────────────────────────────
#  顶层聚合配置
# ──────────────────────────────────────
@dataclass(frozen=True)
class StrategyConfig:
    condition2: Condition2Config = field(default_factory=Condition2Config)
    condition9: Condition9Config = field(default_factory=Condition9Config)
    condition8: Condition8Config = field(default_factory=Condition8Config)
    ma: MaTradingConfig = field(default_factory=MaTradingConfig)
    pyramid: PyramidProfitConfig = field(default_factory=PyramidProfitConfig)
    callback: CallbackAddConfig = field(default_factory=CallbackAddConfig)

# ──────────────────────────────────────
#  工厂函数：从环境变量覆盖默认值
# ──────────────────────────────────────
def load_strategy_config() -> StrategyConfig:
    # 条件2
    c2 = Condition2Config(
        enabled=os.getenv('CONDITION2_ENABLED', 'true').lower() == 'true',
        dynamic_profit_enabled=os.getenv('CONDITION2_DYNAMIC_ENABLED', 'true').lower() == 'true',
        trigger_percent=float(os.getenv('CONDITION2_TRIGGER_PERCENT', 0.0031)),
        decline_percent=float(os.getenv('CONDITION2_DECLINE_PERCENT', 0.001)),
        sell_price_offset=float(os.getenv('CONDITION2_SELL_PRICE_OFFSET', 0.001)),
        max_sell_times=int(os.getenv('CONDITION2_MAX_SELL_TIMES', 1)),
        dynamic_line_threshold=float(os.getenv('CONDITION2_DYNAMIC_LINE_THRESHOLD', 0.025)),
        sell_percent_high=float(os.getenv('CONDITION2_SELL_PERCENT_HIGH', 0.3)),
        sell_percent_low=float(os.getenv('CONDITION2_SELL_PERCENT_LOW', 0.1)),
        next_day_adjustment_enabled=os.getenv('CONDITION2_NEXT_DAY_ADJ_ENABLED', 'true').lower() == 'true',
        next_day_stop_loss_offset=float(os.getenv('CONDITION2_NEXT_DAY_STOP_OFFSET', 0.01)),
        next_day_max_sell_ratio=float(os.getenv('CONDITION2_NEXT_DAY_MAX_SELL_RATIO', 0.5)),
        next_day_max_days=int(os.getenv('CONDITION2_NEXT_DAY_MAX_DAYS', 10)),
    )

    # 条件9
    c9 = Condition9Config(
        enabled=os.getenv('CONDITION9_ENABLED', 'true').lower() == 'true',
        upper_band_percent=float(os.getenv('CONDITION9_UPPER_BAND', 0.02)),
        lower_band_percent=float(os.getenv('CONDITION9_LOWER_BAND', 0.001)),
        trigger_percent=float(os.getenv('CONDITION9_TRIGGER_PERCENT', 0.0015)),
        decline_percent=float(os.getenv('CONDITION9_DECLINE_PERCENT', 0.0004)),
        sell_price_offset=float(os.getenv('CONDITION9_SELL_PRICE_OFFSET', 0.001)),
        dynamic_line_threshold=float(os.getenv('CONDITION9_DYNAMIC_LINE_THRESHOLD', 0.01)),
        sell_percent_high=float(os.getenv('CONDITION9_SELL_PERCENT_HIGH', 0.1)),
        sell_percent_low=float(os.getenv('CONDITION9_SELL_PERCENT_LOW', 0.05)),
        max_sell_times=int(os.getenv('CONDITION9_MAX_SELL_TIMES', 1)),
    )

    # 条件8
    c8 = Condition8Config(
        enabled=os.getenv('CONDITION8_ENABLED', 'true').lower() == 'true',
        max_trade_times=int(os.getenv('CONDITION8_MAX_TRADE_TIMES', 100)),
        rise_percent=float(os.getenv('CONDITION8_RISE_PERCENT', 0.1)),
        decline_percent=float(os.getenv('CONDITION8_DECLINE_PERCENT', 0.1)),
        multiple_order_enabled=os.getenv('CONDITION8_MULTIPLE_ORDER_ENABLED', 'true').lower() == 'true',
        grid_interval_percent=float(os.getenv('CONDITION8_GRID_INTERVAL_PERCENT', 0.01)),
        max_multiple_limit=int(os.getenv('CONDITION8_MAX_MULTIPLE_LIMIT', 10)),
        high_freq_rise=float(os.getenv('CONDITION8_HIGH_FREQ_RISE', 0.12)),
        high_freq_decline=float(os.getenv('CONDITION8_HIGH_FREQ_DECLINE', 0.12)),
        low_freq_rise=float(os.getenv('CONDITION8_LOW_FREQ_RISE', 0.011)),
        low_freq_decline=float(os.getenv('CONDITION8_LOW_FREQ_DECLINE', 0.011)),
        price_band_enabled=os.getenv('CONDITION8_PRICE_BAND_ENABLED', 'true').lower() == 'true',
        upper_band_percent=float(os.getenv('CONDITION8_UPPER_BAND_PERCENT', 0.16)),
        lower_band_percent=float(os.getenv('CONDITION8_LOWER_BAND_PERCENT', 0.16)),
        high_freq_stocks=_parse_env_list(os.getenv('CONDITION8_HIGH_FREQ_STOCKS', '')),
        low_freq_stocks=_parse_env_list(os.getenv('CONDITION8_LOW_FREQ_STOCKS', '')),
        sell_quantity={},  # 可扩展
        buy_quantity={},
        max_total_quantity={},
    )

    # MA 交易
    ma = MaTradingConfig(
        condition4_enabled=os.getenv('CONDITION4_ENABLED', 'false').lower() == 'true',
        condition5_enabled=os.getenv('CONDITION5_ENABLED', 'false').lower() == 'true',
        condition6_enabled=os.getenv('CONDITION6_ENABLED', 'false').lower() == 'true',
        condition7_enabled=os.getenv('CONDITION7_ENABLED', 'false').lower() == 'true',
        buy_below_ma4_qty=int(os.getenv('BUY_BELOW_MA4_QUANTITY', 100)),
        buy_below_ma8_qty=int(os.getenv('BUY_BELOW_MA8_QUANTITY', 100)),
        buy_below_ma12_qty=int(os.getenv('BUY_BELOW_MA12_QUANTITY', 100)),
    )

    # 金字塔
    pyramid = PyramidProfitConfig(
        enabled=os.getenv('PYRAMID_PROFIT_ENABLED', 'true').lower() == 'true',
        sell_price_offset=float(os.getenv('PYRAMID_PROFIT_SELL_PRICE_OFFSET', 0.01)),
        user_base_price={},   # 可从环境变量解析 JSON
        total_quantity={},
    )

    # 动态回调
    callback = CallbackAddConfig(
        enabled=os.getenv('CALLBACK_ADDITION_ENABLED', 'true').lower() == 'true',
        min_trade_unit=int(os.getenv('MIN_TRADE_UNIT', 100)),
        on_condition2=os.getenv('CALLBACK_ON_CONDITION2', 'true').lower() == 'true',
        on_condition9=os.getenv('CALLBACK_ON_CONDITION9', 'true').lower() == 'true',
        on_condition8=os.getenv('CALLBACK_ON_CONDITION8', 'true').lower() == 'true',
        buy_price_offset=float(os.getenv('CALLBACK_BUY_PRICE_OFFSET', 0.01)),
    )

    return StrategyConfig(
        condition2=c2,
        condition9=c9,
        condition8=c8,
        ma=ma,
        pyramid=pyramid,
        callback=callback,
    )

def _parse_env_list(env_value: str) -> List[str]:
    """解析用逗号分隔的股票列表"""
    if not env_value:
        return []
    return [s.strip() for s in env_value.split(',') if s.strip()]