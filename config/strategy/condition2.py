# -*- coding: utf-8 -*-
"""
条件2：动态止盈策略配置模块

包含：条件2启用开关、动态止盈阈值、次日调整机制
"""

# ========== 条件启用开关 ==========
CONDITION2_ENABLED: bool = True  # 是否启用条件2（动态止盈）

# ========== 条件2动态止盈配置 ==========
CONDITION2_DYNAMIC_PROFIT_ENABLED: bool = True  # 是否启用条件2动态止盈
CONDITION2_TRIGGER_PERCENT: float = 0.0031  # 条件2触发动态止盈的涨幅阈值
CONDITION2_DECLINE_PERCENT: float = 0.001  # 条件2动态止盈回落百分比
CONDITION2_SELL_PRICE_OFFSET: float = 0.001  # 条件2卖出价格偏移
MAX_DYNAMIC_PROFIT_SELL_TIMES: int = 1  # 条件2最大卖出次数
CONDITION2_DYNAMIC_LINE_THRESHOLD: float = 0.025  # 条件2动态止盈线阈值
CONDITION2_SELL_PERCENT_HIGH: float = 0.3  # 条件2高位卖出比例
CONDITION2_SELL_PERCENT_LOW: float = 0.1  # 条件2低位卖出比例

# ========== 动态止盈未触发次日基准调整机制配置 ==========
DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED: bool = True  # 是否启用动态止盈次日调整机制
DYNAMIC_PROFIT_NEXT_DAY_STOP_LOSS_PRICE_OFFSET: float = 0.01  # 次日止损价格偏移
DYNAMIC_PROFIT_NEXT_DAY_MAX_SELL_RATIO: float = 0.5  # 次日最大卖出比例
DYNAMIC_PROFIT_NEXT_DAY_MAX_DAYS: int = 10  # 次日调整机制最大延续天数