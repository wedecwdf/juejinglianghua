# -*- coding: utf-8 -*-
"""
策略参数唯一出处 - 拆分版聚合入口

凡涉及邮件、账户、日历、交易时段的参数，已全部移入对应专属模块，
本包仅保留与策略逻辑直接相关的业务参数。

【重要变更】金字塔止盈已完全独立为单独模块，与条件8解除耦合
"""

# ========== 基础配置（股票订阅、系统参数、自动撤单） ==========
from .base import *

# ========== 技术指标参数 ==========
from .indicators import *

# ========== 板数与炸板机制配置 ==========
from .board import *

# ========== 动态回调加仓配置（替代原金字塔加仓） ==========
from .pyramid import *

# ========== 条件2：动态止盈配置 ==========
from .condition2 import *

# ========== 条件4-7：MA均线交易配置 ==========
from .condition4_7 import *

# ========== 条件8：动态基准价网格交易配置 ==========
from .condition8 import *

# ========== 【新增独立模块】金字塔止盈配置（已从条件8剥离） ==========
from .pyramid_profit import *

# ========== 条件9：第一区间动态止盈配置 ==========
from .condition9 import *

# ========== 跨模块参数约束验证（必须在所有导入之后执行） ==========
# ① 高频/低频股票列表无重叠
if ENABLE_HIGH_LOW_FREQUENCY_CLASSIFICATION:
    overlap = set(HIGH_FREQUENCY_STOCKS) & set(LOW_FREQUENCY_STOCKS)
    if overlap:
        raise ValueError(f"高频和低频股票列表存在重叠: {overlap}")

# ② 所有配置股票都有对应的交易数量（动态回调加仓不需要检查金字塔比例）
all_stocks = set(HIGH_FREQUENCY_STOCKS + LOW_FREQUENCY_STOCKS)
for stock in all_stocks:
    if stock not in CONDITION8_SELL_QUANTITY:
        print(f"警告: 股票 {stock} 没有配置条件8卖出数量")
    if stock not in CONDITION8_BUY_QUANTITY:
        print(f"警告: 股票 {stock} 没有配置条件8买入数量")
    if stock not in CONDITION8_MAX_TOTAL_QUANTITY:
        print(f"警告: 股票 {stock} 没有配置条件8最大累计数量")

# ③ 动态回调加仓配置验证（新增）
if CALLBACK_ADDITION_ENABLED:
    if MIN_TRADE_UNIT <= 0:
        raise ValueError("最小交易单位必须大于0")
    print(f"【配置验证】动态回调加仓已启用，最小交易单位: {MIN_TRADE_UNIT}")

# ④ 【新增】金字塔止盈配置验证
if PYRAMID_PROFIT_ENABLED:
    print(f"【配置验证】金字塔止盈已启用，独立运行机制")