# config/strategy/config_objects.py
# -*- coding: utf-8 -*-
"""
策略配置数据类，所有策略参数及技术指标参数均收敛于此。
提供统一的从环境变量加载的函数，消除重复代码。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import os
import logging

logger = logging.getLogger(__name__)

# ---------- 默认技术指标参数 ----------
DEFAULT_MA_PERIODS = [4, 8, 12, 50, 120]
DEFAULT_CCI_PERIOD = 14
DEFAULT_MACD_FAST = 12
DEFAULT_MACD_SLOW = 26
DEFAULT_MACD_SIGNAL = 9
DEFAULT_CCI_UPPER_LIMIT = 100
DEFAULT_CCI_LOWER_LIMIT = -100
DEFAULT_VOLUME_BAR_COUNT = 10
DEFAULT_MACD_HIST_BAR_COUNT = 10

# 默认启用的条件顺序
DEFAULT_ENABLED_CONDITIONS = [
    'next_day_stop_loss',
    'condition2',
    'board_break_sell',
    'condition9',
    'pyramid_add',
    'ma_trading',
    'condition8_grid',
    'pyramid_profit',
    'board_counting',
]

# ---------- 辅助：从环境变量安全取值 ----------
def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).lower() == 'true'

def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, default))

def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))

def _env_list(name: str, default: List[str] = None) -> List[str]:
    if default is None:
        default = []
    val = os.getenv(name, '')
    if not val:
        return default
    return [s.strip() for s in val.split(',') if s.strip()]

# ---------- 技术指标配置 ----------
@dataclass(frozen=True)
class TechIndicatorConfig:
    """技术指标计算参数"""
    ma_periods: List[int] = field(default_factory=lambda: DEFAULT_MA_PERIODS.copy())
    cci_period: int = DEFAULT_CCI_PERIOD
    macd_fast: int = DEFAULT_MACD_FAST
    macd_slow: int = DEFAULT_MACD_SLOW
    macd_signal: int = DEFAULT_MACD_SIGNAL
    cci_upper_limit: int = DEFAULT_CCI_UPPER_LIMIT
    cci_lower_limit: int = DEFAULT_CCI_LOWER_LIMIT
    volume_bar_count: int = DEFAULT_VOLUME_BAR_COUNT
    macd_hist_bar_count: int = DEFAULT_MACD_HIST_BAR_COUNT
    macd_min_period: int = field(init=False)  # 自动计算

    def __post_init__(self):
        # MACD 所需最小数据长度
        object.__setattr__(self, 'macd_min_period', self.macd_slow + self.macd_signal - 1)

    @property
    def max_history_days(self) -> int:
        """计算加载历史数据的最大天数"""
        max_period = max(self.ma_periods + [self.cci_period, self.macd_min_period])
        return max_period * 3

# ---------- 各类交易条件配置（保持不变，但移除默认值中的具体数字依赖） ----------
@dataclass(frozen=True)
class Condition2Config:
    enabled: bool = True
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

@dataclass(frozen=True)
class Condition8Config:
    enabled: bool = True
    max_trade_times: int = 100
    rise_percent: float = 0.0015
    decline_percent: float = 0.0015
    multiple_order_enabled: bool = True
    grid_interval_percent: float = 0.01
    max_multiple_limit: int = 10
    high_freq_rise: float = 0.012
    high_freq_decline: float = 0.012
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

@dataclass(frozen=True)
class MaTradingConfig:
    condition4_enabled: bool = False
    condition5_enabled: bool = False
    condition6_enabled: bool = False
    condition7_enabled: bool = False
    buy_below_ma4_qty: int = 100
    buy_below_ma8_qty: int = 100
    buy_below_ma12_qty: int = 100

@dataclass(frozen=True)
class PyramidProfitConfig:
    enabled: bool = True
    user_base_price: Dict[str, float] = field(default_factory=dict)
    total_quantity: Dict[str, int] = field(default_factory=dict)
    sell_price_offset: float = 0.01
    high_freq_levels: List[float] = field(default_factory=lambda: [0.035, 0.045, 0.065])
    high_freq_ratios: List[float] = field(default_factory=lambda: [0.2, 0.3, 0.5])
    low_freq_levels: List[float] = field(default_factory=lambda: [0.05, 0.07, 0.1])
    low_freq_ratios: List[float] = field(default_factory=lambda: [0.1, 0.2, 0.7])
    default_levels: List[float] = field(default_factory=lambda: [0.02, 0.03, 0.039])
    default_ratios: List[float] = field(default_factory=lambda: [0.1, 0.1, 0.1])

@dataclass(frozen=True)
class CallbackAddConfig:
    enabled: bool = True
    min_trade_unit: int = 100
    on_condition2: bool = True
    on_condition9: bool = True
    on_condition8: bool = True
    buy_price_offset: float = 0.01

@dataclass(frozen=True)
class BoardConfig:
    board_counting_enabled: bool = True
    main_board_limit_up: float = 0.10
    gem_board_limit_up: float = 0.20
    st_board_limit_up: float = 0.05
    bse_board_limit_up: float = 0.30
    limit_up_tolerance: float = 0.005
    min_sealed_duration: int = 30
    max_open_duration: int = 30
    board_break_sell_percent: float = 0.7
    board_break_price_offset: float = 0.02
    dynamic_profit_on_break_enabled: bool = True
    dynamic_profit_sealed_sell_percent: float = 0.5
    dynamic_profit_break_line_sell_percent: float = 0.8
    dynamic_profit_no_action_sell_percent: float = 0.6
    dynamic_profit_decline_percent: float = 0.02
    no_action_sell_time: str = "14:55"
    dynamic_profit_price_offset: float = 0.01
    stage1_enabled: bool = True
    stage2_enabled: bool = True
    board_break_enabled: bool = True
    board_break_low_open_threshold: float = 0.04
    board_break_static_stop_loss_percent: float = 0.05
    board_break_dynamic_profit_decline: float = 0.03
    board_break_static_price_offset: float = 0.05

@dataclass(frozen=True)
class EntryConfig:
    stock_source: str = 'position'
    manual_symbols: List[str] = field(default_factory=list)
    manual_symbols_enabled: bool = False
    sleep_mode: bool = True
    account_data_export_enabled: bool = True
    account_data_export_interval: int = 5
    account_data_export_dir: str = 'account_data'

@dataclass(frozen=True)
class StrategyConfig:
    """顶层策略配置，聚合所有子配置"""
    condition2: Condition2Config = field(default_factory=Condition2Config)
    condition9: Condition9Config = field(default_factory=Condition9Config)
    condition8: Condition8Config = field(default_factory=Condition8Config)
    ma: MaTradingConfig = field(default_factory=MaTradingConfig)
    pyramid: PyramidProfitConfig = field(default_factory=PyramidProfitConfig)
    callback: CallbackAddConfig = field(default_factory=CallbackAddConfig)
    board: BoardConfig = field(default_factory=BoardConfig)
    entry: EntryConfig = field(default_factory=EntryConfig)
    enabled_conditions: List[str] = field(default_factory=lambda: DEFAULT_ENABLED_CONDITIONS.copy())
    tech_indicator: TechIndicatorConfig = field(default_factory=TechIndicatorConfig)


# ---------- 配置加载函数（干净无重复） ----------
def load_strategy_config() -> StrategyConfig:
    """统一从环境变量加载所有配置，默认值由各 dataclass 提供"""

    # ---- 技术指标 ----
    tech = TechIndicatorConfig(
        ma_periods=_env_list('MA_PERIODS', DEFAULT_MA_PERIODS) if 'MA_PERIODS' in os.environ else DEFAULT_MA_PERIODS,
        cci_period=_env_int('CCI_PERIOD', DEFAULT_CCI_PERIOD),
        macd_fast=_env_int('MACD_FAST', DEFAULT_MACD_FAST),
        macd_slow=_env_int('MACD_SLOW', DEFAULT_MACD_SLOW),
        macd_signal=_env_int('MACD_SIGNAL', DEFAULT_MACD_SIGNAL),
        cci_upper_limit=_env_int('CCI_UPPER_LIMIT', DEFAULT_CCI_UPPER_LIMIT),
        cci_lower_limit=_env_int('CCI_LOWER_LIMIT', DEFAULT_CCI_LOWER_LIMIT),
        volume_bar_count=_env_int('VOLUME_BAR_COUNT', DEFAULT_VOLUME_BAR_COUNT),
        macd_hist_bar_count=_env_int('MACD_HIST_BAR_COUNT', DEFAULT_MACD_HIST_BAR_COUNT),
    )

    # ---- 各条件 ----
    c2 = Condition2Config(
        enabled=_env_bool('CONDITION2_ENABLED', Condition2Config.enabled),
        trigger_percent=_env_float('CONDITION2_TRIGGER_PERCENT', Condition2Config.trigger_percent),
        decline_percent=_env_float('CONDITION2_DECLINE_PERCENT', Condition2Config.decline_percent),
        sell_price_offset=_env_float('CONDITION2_SELL_PRICE_OFFSET', Condition2Config.sell_price_offset),
        max_sell_times=_env_int('CONDITION2_MAX_SELL_TIMES', Condition2Config.max_sell_times),
        dynamic_line_threshold=_env_float('CONDITION2_DYNAMIC_LINE_THRESHOLD', Condition2Config.dynamic_line_threshold),
        sell_percent_high=_env_float('CONDITION2_SELL_PERCENT_HIGH', Condition2Config.sell_percent_high),
        sell_percent_low=_env_float('CONDITION2_SELL_PERCENT_LOW', Condition2Config.sell_percent_low),
        next_day_adjustment_enabled=_env_bool('DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED', Condition2Config.next_day_adjustment_enabled),
        next_day_stop_loss_offset=_env_float('NEXT_DAY_STOP_LOSS_OFFSET', Condition2Config.next_day_stop_loss_offset),
        next_day_max_sell_ratio=_env_float('NEXT_DAY_MAX_SELL_RATIO', Condition2Config.next_day_max_sell_ratio),
        next_day_max_days=_env_int('NEXT_DAY_MAX_DAYS', Condition2Config.next_day_max_days),
    )

    c9 = Condition9Config(
        enabled=_env_bool('CONDITION9_ENABLED', Condition9Config.enabled),
        upper_band_percent=_env_float('CONDITION9_UPPER_BAND', Condition9Config.upper_band_percent),
        lower_band_percent=_env_float('CONDITION9_LOWER_BAND', Condition9Config.lower_band_percent),
        trigger_percent=_env_float('CONDITION9_TRIGGER_PERCENT', Condition9Config.trigger_percent),
        decline_percent=_env_float('CONDITION9_DECLINE_PERCENT', Condition9Config.decline_percent),
        sell_price_offset=_env_float('CONDITION9_SELL_PRICE_OFFSET', Condition9Config.sell_price_offset),
        dynamic_line_threshold=_env_float('CONDITION9_DYNAMIC_LINE_THRESHOLD', Condition9Config.dynamic_line_threshold),
        sell_percent_high=_env_float('CONDITION9_SELL_PERCENT_HIGH', Condition9Config.sell_percent_high),
        sell_percent_low=_env_float('CONDITION9_SELL_PERCENT_LOW', Condition9Config.sell_percent_low),
        max_sell_times=_env_int('CONDITION9_MAX_SELL_TIMES', Condition9Config.max_sell_times),
    )

    c8 = Condition8Config(
        enabled=_env_bool('CONDITION8_ENABLED', Condition8Config.enabled),
        max_trade_times=_env_int('CONDITION8_MAX_TRADE_TIMES', Condition8Config.max_trade_times),
        rise_percent=_env_float('CONDITION8_RISE_PERCENT', Condition8Config.rise_percent),
        decline_percent=_env_float('CONDITION8_DECLINE_PERCENT', Condition8Config.decline_percent),
        multiple_order_enabled=_env_bool('CONDITION8_MULTIPLE_ORDER_ENABLED', Condition8Config.multiple_order_enabled),
        grid_interval_percent=_env_float('CONDITION8_GRID_INTERVAL_PERCENT', Condition8Config.grid_interval_percent),
        max_multiple_limit=_env_int('CONDITION8_MAX_MULTIPLE_LIMIT', Condition8Config.max_multiple_limit),
        high_freq_rise=_env_float('CONDITION8_HIGH_FREQ_RISE', Condition8Config.high_freq_rise),
        high_freq_decline=_env_float('CONDITION8_HIGH_FREQ_DECLINE', Condition8Config.high_freq_decline),
        low_freq_rise=_env_float('CONDITION8_LOW_FREQ_RISE', Condition8Config.low_freq_rise),
        low_freq_decline=_env_float('CONDITION8_LOW_FREQ_DECLINE', Condition8Config.low_freq_decline),
        price_band_enabled=_env_bool('CONDITION8_PRICE_BAND_ENABLED', Condition8Config.price_band_enabled),
        upper_band_percent=_env_float('CONDITION8_UPPER_BAND_PERCENT', Condition8Config.upper_band_percent),
        lower_band_percent=_env_float('CONDITION8_LOWER_BAND_PERCENT', Condition8Config.lower_band_percent),
        high_freq_stocks=_env_list('CONDITION8_HIGH_FREQUENCY_STOCKS', Condition8Config.high_freq_stocks),
        low_freq_stocks=_env_list('CONDITION8_LOW_FREQUENCY_STOCKS', Condition8Config.low_freq_stocks),
    )

    ma = MaTradingConfig(
        condition4_enabled=_env_bool('CONDITION4_ENABLED', MaTradingConfig.condition4_enabled),
        condition5_enabled=_env_bool('CONDITION5_ENABLED', MaTradingConfig.condition5_enabled),
        condition6_enabled=_env_bool('CONDITION6_ENABLED', MaTradingConfig.condition6_enabled),
        condition7_enabled=_env_bool('CONDITION7_ENABLED', MaTradingConfig.condition7_enabled),
        buy_below_ma4_qty=_env_int('BUY_BELOW_MA4_QUANTITY', MaTradingConfig.buy_below_ma4_qty),
        buy_below_ma8_qty=_env_int('BUY_BELOW_MA8_QUANTITY', MaTradingConfig.buy_below_ma8_qty),
        buy_below_ma12_qty=_env_int('BUY_BELOW_MA12_QUANTITY', MaTradingConfig.buy_below_ma12_qty),
    )

    pyramid = PyramidProfitConfig(
        enabled=_env_bool('PYRAMID_PROFIT_ENABLED', PyramidProfitConfig.enabled),
        sell_price_offset=_env_float('PYRAMID_PROFIT_SELL_PRICE_OFFSET', PyramidProfitConfig.sell_price_offset),
    )

    callback = CallbackAddConfig(
        enabled=_env_bool('CALLBACK_ADDITION_ENABLED', CallbackAddConfig.enabled),
        min_trade_unit=_env_int('MIN_TRADE_UNIT', CallbackAddConfig.min_trade_unit),
        on_condition2=_env_bool('CALLBACK_ON_CONDITION2', CallbackAddConfig.on_condition2),
        on_condition9=_env_bool('CALLBACK_ON_CONDITION9', CallbackAddConfig.on_condition9),
        on_condition8=_env_bool('CALLBACK_ON_CONDITION8', CallbackAddConfig.on_condition8),
        buy_price_offset=_env_float('CALLBACK_BUY_PRICE_OFFSET', CallbackAddConfig.buy_price_offset),
    )

    board = BoardConfig(
        board_counting_enabled=_env_bool('BOARD_COUNTING_ENABLED', BoardConfig.board_counting_enabled),
        dynamic_profit_on_break_enabled=_env_bool('DYNAMIC_PROFIT_ON_BOARD_BREAK_ENABLED', BoardConfig.dynamic_profit_on_break_enabled),
        board_break_enabled=_env_bool('BOARD_BREAK_ENABLED', BoardConfig.board_break_enabled),
        stage1_enabled=_env_bool('BOARD_BREAK_STAGE1_ENABLED', BoardConfig.stage1_enabled),
        stage2_enabled=_env_bool('BOARD_BREAK_STAGE2_ENABLED', BoardConfig.stage2_enabled),
    )

    entry = EntryConfig(
        stock_source=os.getenv('SYMBOLS_SOURCE', EntryConfig.stock_source),
        manual_symbols=_env_list('MANUAL_SYMBOLS', EntryConfig.manual_symbols),
        manual_symbols_enabled=_env_bool('MANUAL_SYMBOLS_ENABLED', EntryConfig.manual_symbols_enabled),
        sleep_mode=_env_bool('ENABLE_SLEEP_MODE', EntryConfig.sleep_mode),
        account_data_export_enabled=_env_bool('ACCOUNT_DATA_EXPORT_ENABLED', EntryConfig.account_data_export_enabled),
        account_data_export_interval=_env_int('ACCOUNT_DATA_EXPORT_INTERVAL', EntryConfig.account_data_export_interval),
        account_data_export_dir=os.getenv('ACCOUNT_DATA_EXPORT_DIR', EntryConfig.account_data_export_dir),
    )

    enabled_str = os.getenv('ENABLED_CONDITIONS', '')
    if enabled_str:
        enabled_conditions = [s.strip() for s in enabled_str.split(',') if s.strip()]
    else:
        enabled_conditions = DEFAULT_ENABLED_CONDITIONS.copy()

    return StrategyConfig(
        condition2=c2,
        condition9=c9,
        condition8=c8,
        ma=ma,
        pyramid=pyramid,
        callback=callback,
        board=board,
        entry=entry,
        enabled_conditions=enabled_conditions,
        tech_indicator=tech,
    )