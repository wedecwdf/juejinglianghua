# -*- coding: utf-8 -*-
"""
动态回调加仓策略配置模块（原金字塔加仓配置）

机制说明：
- 基于条件2、条件9、条件8分级卖出的实际成交数据动态生成加仓任务
- 不依赖预设固定回调参数，所有阈值动态计算
- 单任务覆盖原则：新卖出成交立即覆盖旧任务
- 炸板动态止盈卖出和断板动态止盈卖出不参与本机制
"""
from typing import List, Dict, Any

# ========== 动态回调加仓总开关 ==========
CALLBACK_ADDITION_ENABLED: bool = True  # 是否启用动态回调加仓

# ========== 基础交易参数 ==========
MIN_TRADE_UNIT: int = 100  # 最小交易单位（股）

# ========== 触发条件配置（哪些条件的卖出可生成回调加仓任务） ==========
# 条件2（动态止盈）卖出后生成回调加仓任务
CALLBACK_ON_CONDITION2: bool = True

# 条件9（第一区间动态止盈）卖出后生成回调加仓任务
CALLBACK_ON_CONDITION9: bool = True

# 条件8（分级止盈）卖出后生成回调加仓任务
CALLBACK_ON_CONDITION8: bool = True

# ========== 排除条件配置（明确不参与机制的类型） ==========
# 以下卖出类型不参与动态回调加仓（文档强制规定）：
# - 炸板动态止盈卖出（board_dynamic_profit）
# - 断板机制卖出（board_break_static / board_break_dynamic）

# ========== 买入触发执行配置 ==========
CALLBACK_BUY_PRICE_OFFSET: float = 0.01  # 买入委托价格偏移（为确保持续使用）

# ========== 数据精度配置 ==========
PRICE_DECIMAL_PRECISION: int = 4  # 价格计算保留小数位