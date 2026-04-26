# -*- coding: utf-8 -*-
"""
条件9：第一区间动态止盈策略配置模块

包含：条件9启用开关、价格区间、触发阈值、卖出比例等
"""

# ========== 条件启用开关 ==========
CONDITION9_ENABLED: bool = True  # 是否启用条件9（第一区间动态止盈）

# ========== 第一区间动态止盈机制配置 ==========
CONDITION9_UPPER_BAND_PERCENT: float = 0.02  # 条件9价格区间上限百分比
CONDITION9_LOWER_BAND_PERCENT: float = 0.001  # 条件9价格区间下限百分比
CONDITION9_TRIGGER_PERCENT: float = 0.0015  # 条件9触发动态止盈的涨幅阈值
CONDITION9_DECLINE_PERCENT: float = 0.0004  # 条件9动态止盈回落百分比
CONDITION9_SELL_PRICE_OFFSET: float = 0.001  # 条件9卖出价格偏移
CONDITION9_DYNAMIC_LINE_THRESHOLD: float = 0.01  # 条件9动态止盈线阈值
CONDITION9_SELL_PERCENT_HIGH: float = 0.1  # 条件9高位卖出比例
CONDITION9_SELL_PERCENT_LOW: float = 0.05  # 条件9低位卖出比例
MAX_CONDITION9_SELL_TIMES: int = 1  # 条件9最大卖出次数

# ========== 自适应下跌买入触发间距调整配置 ==========
ADAPTIVE_DROP_SPACING_ENABLED: bool = True  # 是否启用自适应下跌买入触发间距调整
CONDITION2_DROP_MULTIPLIER: float = 1.7  # 条件2触发后下跌买入幅度扩大倍数
CONDITION9_DROP_MULTIPLIER: float = 1.2  # 条件9触发后下跌买入幅度扩大倍数