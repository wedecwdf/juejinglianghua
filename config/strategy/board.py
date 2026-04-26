# -*- coding: utf-8 -*-
"""
板数、炸板、断板机制配置模块

包含：涨停板计数、炸板动态止盈、断板静态止损相关参数
"""

# ========== 板数机制配置 ==========
BOARD_COUNTING_ENABLED: bool = True  # 是否启用板数计数
MAIN_BOARD_LIMIT_UP_PERCENT: float = 0.10  # 主板涨停百分比
GEM_BOARD_LIMIT_UP_PERCENT: float = 0.20  # 创业板涨停百分比
ST_BOARD_LIMIT_UP_PERCENT: float = 0.05  # ST股涨停百分比
BSE_BOARD_LIMIT_UP_PERCENT: float = 0.30  # 北交所涨停百分比
LIMIT_UP_TOLERANCE_PERCENT: float = 0.005  # 涨停价格容忍度百分比
MIN_SEALED_DURATION: int = 30  # 最小封板持续时间（分钟）
MAX_OPEN_DURATION: int = 30  # 最大开板持续时间（分钟）
BOARD_BREAK_SELL_PERCENT: float = 0.7  # 断板卖出比例
BOARD_BREAK_PRICE_OFFSET: float = 0.02  # 断板卖出价格偏移

# ========== 炸板后动态止盈机制配置 ==========
DYNAMIC_PROFIT_ON_BOARD_BREAK_ENABLED: bool = True  # 是否启用炸板后动态止盈
DYNAMIC_PROFIT_SEALED_SELL_PERCENT: float = 0.5  # 再次封板动态止盈卖出比例
DYNAMIC_PROFIT_BREAK_LINE_SELL_PERCENT: float = 0.8  # 跌破止盈线动态止盈卖出比例
DYNAMIC_PROFIT_NO_ACTION_SELL_PERCENT: float = 0.6  # 无动作动态止盈卖出比例

BOARD_BREAK_DYNAMIC_PROFIT_DECLINE_PERCENT: float = 0.02  # 炸板后动态止盈回落百分比阈值（默认1.5%）
BOARD_BREAK_NO_ACTION_SELL_TIME: str = "14:55"  # 炸板后无动作卖出时间阈值（格式HH:MM）
BOARD_BREAK_DYNAMIC_PROFIT_PRICE_OFFSET: float = 0.01  # 炸板后动态止盈卖出价格偏移（默认0.01元）

# ========== 炸板动态止盈阶段配置（新增） ==========
BOARD_BREAK_STAGE1_ENABLED: bool = True  # 是否启用阶段①（开板立即触发机制）
BOARD_BREAK_STAGE2_ENABLED: bool = True  # 是否启用阶段②（炸板确认接管机制）

# ========== 断板机制配置 ==========
BOARD_BREAK_ENABLED: bool = True  # 是否启用断板机制
BOARD_BREAK_LOW_OPEN_THRESHOLD: float = 0.04  # 断板低开阈值
BOARD_BREAK_STATIC_STOP_LOSS_PERCENT: float = 0.05  # 断板静态止损百分比
BOARD_BREAK_DYNAMIC_PROFIT_DECLINE_PERCENT: float = 0.03  # 断板动态止盈回落百分比
BOARD_BREAK_STATIC_PRICE_OFFSET: float = 0.05  # 断板静态止损价格偏移