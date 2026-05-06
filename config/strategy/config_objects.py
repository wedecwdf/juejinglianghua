# config/strategy/config_objects.py
# -*- coding: utf-8 -*-
"""
策略配置数据类，所有策略参数均收敛于此，支持环境变量覆盖。

- 修改配置时，直接修改对应数据类的默认值即可，无需改动加载函数。
- 可通过 .env 或系统环境变量动态覆盖。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import os
import logging

logger = logging.getLogger(__name__)

# 默认启用的条件顺序（与 StrategyConfig 中定义的默认值保持一致）
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

# ---------- 条件配置 ----------

@dataclass(frozen=True)
class Condition2Config:
    """条件2：动态止盈配置"""

    # 是否启用条件2
    enabled: bool = True
    # 触发动态止盈监控的涨幅阈值（例如0.0031即0.31%）
    trigger_percent: float = 0.0031
    # 从最高点回落的比例，用于计算动态止盈线（例如0.001即0.1%）
    decline_percent: float = 0.001
    # 卖出委托价格相对于当前价的偏移量（向下偏移）
    sell_price_offset: float = 0.001
    # 动态止盈最多卖出次数
    max_sell_times: int = 1
    # 动态止盈线涨幅阈值，用于区分高/低卖出比例
    dynamic_line_threshold: float = 0.025
    # 当止盈线涨幅 >= 阈值时，卖出当前持仓的比例
    sell_percent_high: float = 0.3
    # 当止盈线涨幅 < 阈值时，卖出当前持仓的比例
    sell_percent_low: float = 0.1
    # 是否启用次日调整机制（基于条件2/9的最高止盈线设置次日固定止损）
    next_day_adjustment_enabled: bool = True
    # 次日调整机制中的止损价偏移量（低于最高止盈线的幅度）
    next_day_stop_loss_offset: float = 0.01
    # 次日调整机制的最大卖出比例（叠加条件2和条件9的比例上限）
    next_day_max_sell_ratio: float = 0.5
    # 次日调整机制的最大延续天数
    next_day_max_days: int = 10


@dataclass(frozen=True)
class Condition9Config:
    """条件9：第一区间动态止盈配置"""

    # 是否启用条件9
    enabled: bool = True
    # 条件9监测区间的上限比例（相对基准价）
    upper_band_percent: float = 0.02
    # 条件9监测区间的下限比例（相对基准价）
    lower_band_percent: float = 0.001
    # 触发动态止盈监控的涨幅阈值
    trigger_percent: float = 0.0015
    # 从最高点回落的比例，用于计算动态止盈线
    decline_percent: float = 0.0004
    # 卖出委托价格偏移量
    sell_price_offset: float = 0.001
    # 止盈线涨幅阈值，用于区分高/低卖出比例
    dynamic_line_threshold: float = 0.01
    # 高涨幅时的卖出比例
    sell_percent_high: float = 0.1
    # 低涨幅时的卖出比例
    sell_percent_low: float = 0.05
    # 条件9最多卖出次数
    max_sell_times: int = 1


@dataclass(frozen=True)
class Condition8Config:
    """条件8：动态基准价网格交易配置"""

    # 是否启用条件8
    enabled: bool = True
    # 条件8允许的最大交易次数（当日总买卖次数上限）
    max_trade_times: int = 100
    # 默认上涨触发阈值（基准价变动比例）
    rise_percent: float = 0.0015
    # 默认下跌触发阈值
    decline_percent: float = 0.0015
    # 是否启用倍数委托（跳过网格时放大数量）
    multiple_order_enabled: bool = True
    # 网格间隔百分比（用于计算跳过网格数）
    grid_interval_percent: float = 0.01
    # 倍数委托的最大倍数上限
    max_multiple_limit: int = 10
    # 高频股票专属的上涨阈值
    high_freq_rise: float = 0.012
    # 高频股票专属的下跌阈值
    high_freq_decline: float = 0.012
    # 低频股票专属的上涨阈值
    low_freq_rise: float = 0.011
    # 低频股票专属的下跌阈值
    low_freq_decline: float = 0.011
    # 是否启用价格区间（超出区间后休眠）
    price_band_enabled: bool = True
    # 价格区间的上限比例（相对基准价）
    upper_band_percent: float = 0.16
    # 价格区间的下限比例（相对基准价）
    lower_band_percent: float = 0.16
    # 高频股票列表（代码列表）
    high_freq_stocks: List[str] = field(default_factory=list)
    # 低频股票列表（代码列表）
    low_freq_stocks: List[str] = field(default_factory=list)
    # 各股票的条件8卖出基础数量（{symbol: quantity}）
    sell_quantity: Dict[str, int] = field(default_factory=dict)
    # 各股票的条件8买入基础数量（{symbol: quantity}）
    buy_quantity: Dict[str, int] = field(default_factory=dict)
    # 各股票的条件8当日总买入/卖出数量上限（{symbol: quantity}）
    max_total_quantity: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class MaTradingConfig:
    """MA均线交易条件（条件4-7）配置"""

    # 是否启用条件4（低于MA4买入）
    condition4_enabled: bool = False
    # 是否启用条件5（低于MA8买入）
    condition5_enabled: bool = False
    # 是否启用条件6（低于MA12买入）
    condition6_enabled: bool = False
    # 是否启用条件7（14:54后低于MA4卖出）
    condition7_enabled: bool = False
    # 条件4买入的固定股数
    buy_below_ma4_qty: int = 100
    # 条件5买入的固定股数
    buy_below_ma8_qty: int = 100
    # 条件6买入的固定股数
    buy_below_ma12_qty: int = 100


@dataclass(frozen=True)
class PyramidProfitConfig:
    """金字塔止盈配置（独立止盈机制）"""

    # 是否启用金字塔止盈
    enabled: bool = True
    # 用户自定义的各股票基准价（{symbol: price}）
    user_base_price: Dict[str, float] = field(default_factory=dict)
    # 各股票的总持仓数量（用于计算各级卖出股数）
    total_quantity: Dict[str, int] = field(default_factory=dict)
    # 卖出委托价格偏移量
    sell_price_offset: float = 0.01
    # 高频股票的止盈涨幅台阶
    high_freq_levels: List[float] = field(default_factory=lambda: [0.035, 0.045, 0.065])
    # 高频股票各级台阶的卖出比例
    high_freq_ratios: List[float] = field(default_factory=lambda: [0.2, 0.3, 0.5])
    # 低频股票的止盈涨幅台阶
    low_freq_levels: List[float] = field(default_factory=lambda: [0.05, 0.07, 0.1])
    # 低频股票各级台阶的卖出比例
    low_freq_ratios: List[float] = field(default_factory=lambda: [0.1, 0.2, 0.7])
    # 默认股票（非高/低频）的止盈涨幅台阶
    default_levels: List[float] = field(default_factory=lambda: [0.02, 0.03, 0.039])
    # 默认股票各级台阶的卖出比例
    default_ratios: List[float] = field(default_factory=lambda: [0.1, 0.1, 0.1])


@dataclass(frozen=True)
class CallbackAddConfig:
    """动态回调加仓配置（卖出后等待回调买入）"""

    # 是否启用动态回调加仓
    enabled: bool = True
    # 最小交易单位（股数，低于此数量不创建任务）
    min_trade_unit: int = 100
    # 是否允许基于条件2卖出创建回调任务
    on_condition2: bool = True
    # 是否允许基于条件9卖出创建回调任务
    on_condition9: bool = True
    # 是否允许基于条件8卖出创建回调任务
    on_condition8: bool = True
    # 买入委托价格偏移量（高于触发价的部分）
    buy_price_offset: float = 0.01


@dataclass(frozen=True)
class BoardConfig:
    """板数、断板、炸板相关配置"""

    # 是否启用板数计数
    board_counting_enabled: bool = True
    # 主板涨停幅度
    main_board_limit_up: float = 0.10
    # 创业板/科创板涨停幅度
    gem_board_limit_up: float = 0.20
    # ST股票涨停幅度
    st_board_limit_up: float = 0.05
    # 北交所涨停幅度
    bse_board_limit_up: float = 0.30
    # 涨停价判定容差比例
    limit_up_tolerance: float = 0.005
    # 有效封板最短持续时间（分钟）
    min_sealed_duration: int = 30
    # 开板后判定为炸板的最长持续时间（分钟）
    max_open_duration: int = 30
    # 断板静态止损的卖出比例
    board_break_sell_percent: float = 0.7
    # 断板卖出价格偏移量
    board_break_price_offset: float = 0.02
    # 是否启用炸板动态止盈
    dynamic_profit_on_break_enabled: bool = True
    # 阶段②再次封板时的卖出比例
    dynamic_profit_sealed_sell_percent: float = 0.5
    # 阶段①/②跌破止盈线时的卖出比例
    dynamic_profit_break_line_sell_percent: float = 0.8
    # 阶段②尾盘无动作时的卖出比例
    dynamic_profit_no_action_sell_percent: float = 0.6
    # 炸板动态止盈的回落比例
    dynamic_profit_decline_percent: float = 0.02
    # 阶段②尾盘无动作的触发时间（如"14:55"）
    no_action_sell_time: str = "14:55"
    # 炸板动态止盈的卖出价格偏移量
    dynamic_profit_price_offset: float = 0.01
    # 是否启用阶段①
    stage1_enabled: bool = True
    # 是否启用阶段②
    stage2_enabled: bool = True
    # 是否启用断板机制（次日低开或未涨停时的静态止损与动态止盈）
    board_break_enabled: bool = True
    # 断板次日大幅低开阈值（用于判定是否立即止损）
    board_break_low_open_threshold: float = 0.04
    # 断板静态止损的跌幅比例
    board_break_static_stop_loss_percent: float = 0.05
    # 断板动态止盈的回落比例
    board_break_dynamic_profit_decline: float = 0.03
    # 断板静态止损的卖出价格偏移量
    board_break_static_price_offset: float = 0.05


@dataclass(frozen=True)
class EntryConfig:
    """入口配置：股票来源、休眠模式、数据导出等"""

    # 股票代码来源模式：'position'、'manual' 或 'both'
    stock_source: str = 'position'
    # 手动输入的股票代码列表
    manual_symbols: List[str] = field(default_factory=list)
    # 是否启用手动输入股票列表
    manual_symbols_enabled: bool = False
    # 是否启用休眠模式（午间休市和收盘后自动休眠）
    sleep_mode: bool = True
    # 是否启用账户数据定时导出
    account_data_export_enabled: bool = True
    # 账户数据导出间隔（秒）
    account_data_export_interval: int = 5
    # 账户数据导出目录
    account_data_export_dir: str = 'account_data'


@dataclass(frozen=True)
class StrategyConfig:
    """顶层策略配置，聚合所有子配置"""

    # 条件2配置
    condition2: Condition2Config = field(default_factory=Condition2Config)
    # 条件9配置
    condition9: Condition9Config = field(default_factory=Condition9Config)
    # 条件8配置
    condition8: Condition8Config = field(default_factory=Condition8Config)
    # MA均线交易配置
    ma: MaTradingConfig = field(default_factory=MaTradingConfig)
    # 金字塔止盈配置
    pyramid: PyramidProfitConfig = field(default_factory=PyramidProfitConfig)
    # 动态回调加仓配置
    callback: CallbackAddConfig = field(default_factory=CallbackAddConfig)
    # 板数/断板/炸板配置
    board: BoardConfig = field(default_factory=BoardConfig)
    # 入口配置
    entry: EntryConfig = field(default_factory=EntryConfig)
    # 启用的条件列表（按名称顺序，决定执行优先级）
    enabled_conditions: List[str] = field(default_factory=lambda: DEFAULT_ENABLED_CONDITIONS.copy())


# 辅助函数：解析环境变量中的逗号分隔列表
def _parse_env_list(env_value: str) -> List[str]:
    if not env_value:
        return []
    return [s.strip() for s in env_value.split(',') if s.strip()]


def load_strategy_config() -> StrategyConfig:
    """
    从环境变量加载策略配置，所有默认值均取自配置类的定义。
    用户只需在对应类中修改参数即可，无需同步修改本函数。
    """

    # 创建各类默认实例，用于提取默认值
    default_c2 = Condition2Config()
    default_c9 = Condition9Config()
    default_c8 = Condition8Config()
    default_ma = MaTradingConfig()
    default_pyramid = PyramidProfitConfig()
    default_callback = CallbackAddConfig()
    default_board = BoardConfig()
    default_entry = EntryConfig()

    # ---------- 条件2 ----------
    c2 = Condition2Config(
        enabled=os.getenv('CONDITION2_ENABLED', str(default_c2.enabled)).lower() == 'true',
        trigger_percent=float(os.getenv('CONDITION2_TRIGGER_PERCENT', default_c2.trigger_percent)),
        decline_percent=float(os.getenv('CONDITION2_DECLINE_PERCENT', default_c2.decline_percent)),
        sell_price_offset=float(os.getenv('CONDITION2_SELL_PRICE_OFFSET', default_c2.sell_price_offset)),
        max_sell_times=int(os.getenv('CONDITION2_MAX_SELL_TIMES', default_c2.max_sell_times)),
        dynamic_line_threshold=float(os.getenv('CONDITION2_DYNAMIC_LINE_THRESHOLD', default_c2.dynamic_line_threshold)),
        sell_percent_high=float(os.getenv('CONDITION2_SELL_PERCENT_HIGH', default_c2.sell_percent_high)),
        sell_percent_low=float(os.getenv('CONDITION2_SELL_PERCENT_LOW', default_c2.sell_percent_low)),
        next_day_adjustment_enabled=os.getenv('DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED', str(default_c2.next_day_adjustment_enabled)).lower() == 'true',
        next_day_stop_loss_offset=float(os.getenv('NEXT_DAY_STOP_LOSS_OFFSET', default_c2.next_day_stop_loss_offset)),
        next_day_max_sell_ratio=float(os.getenv('NEXT_DAY_MAX_SELL_RATIO', default_c2.next_day_max_sell_ratio)),
        next_day_max_days=int(os.getenv('NEXT_DAY_MAX_DAYS', default_c2.next_day_max_days)),
    )

    # ---------- 条件9 ----------
    c9 = Condition9Config(
        enabled=os.getenv('CONDITION9_ENABLED', str(default_c9.enabled)).lower() == 'true',
        upper_band_percent=float(os.getenv('CONDITION9_UPPER_BAND', default_c9.upper_band_percent)),
        lower_band_percent=float(os.getenv('CONDITION9_LOWER_BAND', default_c9.lower_band_percent)),
        trigger_percent=float(os.getenv('CONDITION9_TRIGGER_PERCENT', default_c9.trigger_percent)),
        decline_percent=float(os.getenv('CONDITION9_DECLINE_PERCENT', default_c9.decline_percent)),
        sell_price_offset=float(os.getenv('CONDITION9_SELL_PRICE_OFFSET', default_c9.sell_price_offset)),
        dynamic_line_threshold=float(os.getenv('CONDITION9_DYNAMIC_LINE_THRESHOLD', default_c9.dynamic_line_threshold)),
        sell_percent_high=float(os.getenv('CONDITION9_SELL_PERCENT_HIGH', default_c9.sell_percent_high)),
        sell_percent_low=float(os.getenv('CONDITION9_SELL_PERCENT_LOW', default_c9.sell_percent_low)),
        max_sell_times=int(os.getenv('CONDITION9_MAX_SELL_TIMES', default_c9.max_sell_times)),
    )

    # ---------- 条件8 ----------
    c8 = Condition8Config(
        enabled=os.getenv('CONDITION8_ENABLED', str(default_c8.enabled)).lower() == 'true',
        max_trade_times=int(os.getenv('CONDITION8_MAX_TRADE_TIMES', default_c8.max_trade_times)),
        rise_percent=float(os.getenv('CONDITION8_RISE_PERCENT', default_c8.rise_percent)),
        decline_percent=float(os.getenv('CONDITION8_DECLINE_PERCENT', default_c8.decline_percent)),
        multiple_order_enabled=os.getenv('CONDITION8_MULTIPLE_ORDER_ENABLED', str(default_c8.multiple_order_enabled)).lower() == 'true',
        grid_interval_percent=float(os.getenv('CONDITION8_GRID_INTERVAL_PERCENT', default_c8.grid_interval_percent)),
        max_multiple_limit=int(os.getenv('CONDITION8_MAX_MULTIPLE_LIMIT', default_c8.max_multiple_limit)),
        high_freq_rise=float(os.getenv('CONDITION8_HIGH_FREQ_RISE', default_c8.high_freq_rise)),
        high_freq_decline=float(os.getenv('CONDITION8_HIGH_FREQ_DECLINE', default_c8.high_freq_decline)),
        low_freq_rise=float(os.getenv('CONDITION8_LOW_FREQ_RISE', default_c8.low_freq_rise)),
        low_freq_decline=float(os.getenv('CONDITION8_LOW_FREQ_DECLINE', default_c8.low_freq_decline)),
        price_band_enabled=os.getenv('CONDITION8_PRICE_BAND_ENABLED', str(default_c8.price_band_enabled)).lower() == 'true',
        upper_band_percent=float(os.getenv('CONDITION8_UPPER_BAND_PERCENT', default_c8.upper_band_percent)),
        lower_band_percent=float(os.getenv('CONDITION8_LOWER_BAND_PERCENT', default_c8.lower_band_percent)),
        high_freq_stocks=_parse_env_list(os.getenv('CONDITION8_HIGH_FREQ_STOCKS', '')) or default_c8.high_freq_stocks,
        low_freq_stocks=_parse_env_list(os.getenv('CONDITION8_LOW_FREQ_STOCKS', '')) or default_c8.low_freq_stocks,
    )

    # ---------- MA均线 ----------
    ma = MaTradingConfig(
        condition4_enabled=os.getenv('CONDITION4_ENABLED', str(default_ma.condition4_enabled)).lower() == 'true',
        condition5_enabled=os.getenv('CONDITION5_ENABLED', str(default_ma.condition5_enabled)).lower() == 'true',
        condition6_enabled=os.getenv('CONDITION6_ENABLED', str(default_ma.condition6_enabled)).lower() == 'true',
        condition7_enabled=os.getenv('CONDITION7_ENABLED', str(default_ma.condition7_enabled)).lower() == 'true',
        buy_below_ma4_qty=int(os.getenv('BUY_BELOW_MA4_QUANTITY', default_ma.buy_below_ma4_qty)),
        buy_below_ma8_qty=int(os.getenv('BUY_BELOW_MA8_QUANTITY', default_ma.buy_below_ma8_qty)),
        buy_below_ma12_qty=int(os.getenv('BUY_BELOW_MA12_QUANTITY', default_ma.buy_below_ma12_qty)),
    )

    # ---------- 金字塔止盈 ----------
    pyramid = PyramidProfitConfig(
        enabled=os.getenv('PYRAMID_PROFIT_ENABLED', str(default_pyramid.enabled)).lower() == 'true',
        sell_price_offset=float(os.getenv('PYRAMID_PROFIT_SELL_PRICE_OFFSET', default_pyramid.sell_price_offset)),
    )

    # ---------- 动态回调加仓 ----------
    callback = CallbackAddConfig(
        enabled=os.getenv('CALLBACK_ADDITION_ENABLED', str(default_callback.enabled)).lower() == 'true',
        min_trade_unit=int(os.getenv('MIN_TRADE_UNIT', default_callback.min_trade_unit)),
        on_condition2=os.getenv('CALLBACK_ON_CONDITION2', str(default_callback.on_condition2)).lower() == 'true',
        on_condition9=os.getenv('CALLBACK_ON_CONDITION9', str(default_callback.on_condition9)).lower() == 'true',
        on_condition8=os.getenv('CALLBACK_ON_CONDITION8', str(default_callback.on_condition8)).lower() == 'true',
        buy_price_offset=float(os.getenv('CALLBACK_BUY_PRICE_OFFSET', default_callback.buy_price_offset)),
    )

    # ---------- 板数/断板/炸板 ----------
    board = BoardConfig(
        board_counting_enabled=os.getenv('BOARD_COUNTING_ENABLED', str(default_board.board_counting_enabled)).lower() == 'true',
        dynamic_profit_on_break_enabled=os.getenv('DYNAMIC_PROFIT_ON_BOARD_BREAK_ENABLED', str(default_board.dynamic_profit_on_break_enabled)).lower() == 'true',
        board_break_enabled=os.getenv('BOARD_BREAK_ENABLED', str(default_board.board_break_enabled)).lower() == 'true',
        stage1_enabled=os.getenv('BOARD_BREAK_STAGE1_ENABLED', str(default_board.stage1_enabled)).lower() == 'true',
        stage2_enabled=os.getenv('BOARD_BREAK_STAGE2_ENABLED', str(default_board.stage2_enabled)).lower() == 'true',
    )

    # ---------- 入口配置 ----------
    entry = EntryConfig(
        stock_source=os.getenv('SYMBOLS_SOURCE', default_entry.stock_source),
        manual_symbols=_parse_env_list(os.getenv('MANUAL_SYMBOLS', '')) or default_entry.manual_symbols,
        manual_symbols_enabled=os.getenv('MANUAL_SYMBOLS_ENABLED', str(default_entry.manual_symbols_enabled)).lower() == 'true',
        sleep_mode=os.getenv('ENABLE_SLEEP_MODE', str(default_entry.sleep_mode)).lower() == 'true',
        account_data_export_enabled=os.getenv('ACCOUNT_DATA_EXPORT_ENABLED', str(default_entry.account_data_export_enabled)).lower() == 'true',
        account_data_export_interval=int(os.getenv('ACCOUNT_DATA_EXPORT_INTERVAL', default_entry.account_data_export_interval)),
        account_data_export_dir=os.getenv('ACCOUNT_DATA_EXPORT_DIR', default_entry.account_data_export_dir),
    )

    # ---------- 启用的条件列表 ----------
    enabled_str = os.getenv('ENABLED_CONDITIONS', '')
    if enabled_str:
        enabled_conditions = [s.strip() for s in enabled_str.split(',') if s.strip()]
    else:
        # 使用模块级常量（与 StrategyConfig 默认值一致）
        enabled_conditions = DEFAULT_ENABLED_CONDITIONS.copy()

    # 组装并返回完整的策略配置
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
    )