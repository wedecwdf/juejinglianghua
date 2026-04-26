# -*- coding: utf-8 -*-
"""
条件8：动态基准价网格交易策略配置模块（核心大模块）

包含：基础网格参数、高频/低频独立阈值、倍数委托、
价格区间、间距调整等

【修改说明】金字塔止盈机制已完全独立，移除了所有金字塔止盈相关配置
"""

import os
from typing import List, Dict

# ========== 条件启用开关 ==========
CONDITION8_ENABLED: bool = True  # 是否启用条件8（动态基准价交易）

# ========== 基础网格参数 ==========
MAX_CONDITION8_TRADE_TIMES: int = 100  # 条件8最大交易次数
CONDITION8_RISE_PERCENT: float = 0.1  # 默认上涨触发百分比（1.6%）
CONDITION8_DECLINE_PERCENT: float = 0.1  # 默认下跌触发百分比（1.5%）

# ========== 条件八倍数委托功能配置 ==========
CONDITION8_MULTIPLE_ORDER_ENABLED: bool = True  # 是否启用倍数委托功能
CONDITION8_GRID_INTERVAL_PERCENT: float = 0.01  # 价格网格间隔比例（默认1%）
CONDITION8_MAX_MULTIPLE_LIMIT: int = 10  # 最大倍数限制值

# 高频/低频股票专用网格间隔配置
CONDITION8_HIGH_FREQ_GRID_INTERVAL: float = 0.01  # 高频股票网格间隔（0.5%）
CONDITION8_LOW_FREQ_GRID_INTERVAL: float = 0.01  # 低频股票网格间隔（1.5%）

# ========== 条件八高频/低频独立涨跌幅阈值配置 ==========
# 高频股票涨跌幅阈值
CONDITION8_HIGH_FREQ_RISE_PERCENT: float = 0.0012  # 高频股票上涨触发百分比（默认1.2%）
CONDITION8_HIGH_FREQ_DECLINE_PERCENT: float = 0.0012  # 高频股票下跌触发百分比（默认1.2%）

# 低频股票涨跌幅阈值
CONDITION8_LOW_FREQ_RISE_PERCENT: float = 0.0011  # 低频股票上涨触发百分比（默认2.0%）
CONDITION8_LOW_FREQ_DECLINE_PERCENT: float = 0.0011  # 低频股票下跌触发百分比（默认2.0%）

# ========== 高频/低频股票统一配置 ==========
ENABLE_HIGH_LOW_FREQUENCY_CLASSIFICATION: bool = True  # 是否启用高/低频股票分类

# 【修改点】从环境变量读取股票列表，支持逗号分隔
def _parse_env_stock_list(env_var: str) -> List[str]:
    """从环境变量解析股票列表，支持逗号分隔并去除空白"""
    value = os.getenv(env_var, "")
    if not value:
        return []
    return [s.strip() for s in value.split(',') if s.strip()]

HIGH_FREQUENCY_STOCKS: List[str] = _parse_env_stock_list("CONDITION8_HIGH_FREQUENCY_STOCKS")
LOW_FREQUENCY_STOCKS: List[str] = _parse_env_stock_list("CONDITION8_LOW_FREQUENCY_STOCKS")

# 条件8动态基准价交易数量配置（高频）
TRADING_HIGH_FREQ_QUANTITY: Dict[str, int] = {  # 高频股票交易数量配置
    'sell_quantity': 100,  # 卖出数量
    'buy_quantity': 100,  # 买入数量
    'max_total_quantity': 5000  # 最大累计数量
}

# 条件8动态基准价交易数量配置（低频）
TRADING_LOW_FREQ_QUANTITY: Dict[str, int] = {  # 低频股票交易数量配置
    'sell_quantity': 100,  # 卖出数量
    'buy_quantity': 100,  # 买入数量
    'max_total_quantity': 10000  # 最大累计数量
}

# 动态生成股票级配置（保持向后兼容）
CONDITION8_SELL_QUANTITY: Dict[str, int] = {}  # 条件8卖出数量
CONDITION8_BUY_QUANTITY: Dict[str, int] = {}  # 条件8买入数量
CONDITION8_MAX_TOTAL_QUANTITY: Dict[str, int] = {}  # 条件8最大累计数量

# 初始化高频/低频股票数量映射
if ENABLE_HIGH_LOW_FREQUENCY_CLASSIFICATION:
    for stock in HIGH_FREQUENCY_STOCKS:
        CONDITION8_SELL_QUANTITY[stock] = TRADING_HIGH_FREQ_QUANTITY['sell_quantity']
        CONDITION8_BUY_QUANTITY[stock] = TRADING_HIGH_FREQ_QUANTITY['buy_quantity']
        CONDITION8_MAX_TOTAL_QUANTITY[stock] = TRADING_HIGH_FREQ_QUANTITY['max_total_quantity']
    for stock in LOW_FREQUENCY_STOCKS:
        CONDITION8_SELL_QUANTITY[stock] = TRADING_LOW_FREQ_QUANTITY['sell_quantity']
        CONDITION8_BUY_QUANTITY[stock] = TRADING_LOW_FREQ_QUANTITY['buy_quantity']
        CONDITION8_MAX_TOTAL_QUANTITY[stock] = TRADING_LOW_FREQ_QUANTITY['max_total_quantity']

# ========== 条件8价格区间配置 ==========
CONDITION8_PRICE_BAND_ENABLED: bool = True  # 是否启用条件8价格区间功能
CONDITION8_UPPER_BAND_PERCENT: float = 0.16  # 条件8价格区间上限百分比
CONDITION8_LOWER_BAND_PERCENT: float = 0.16  # 条件8价格区间下限百分比

# ========== 条件八间距调整机制配置 ==========
CONDITION8_ADJUSTMENT_ENABLED: bool = True  # 是否启用条件8间距调整机制
CONDITION8_ADJUSTMENT_EXPIRY_DAYS: int = 1  # 条件8调整过期天数
CONDITION8_SLEEP_DAYS: int = 1  # 条件8休眠天数
CONDITION8_ADJUSTMENT_FILE: str = "condition8_adjustment.json"  # 条件8调整数据文件