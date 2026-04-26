# -*- coding: utf-8 -*-
"""
条件4-7：MA均线交易策略配置模块

包含：条件4（低于MA4买入）、条件5（低于MA8买入）、
      条件6（低于MA12买入）、条件7（14:54后低于MA4卖出）
"""

# ========== 条件启用开关 ==========
CONDITION4_ENABLED: bool = False  # 是否启用条件4（低于MA4买入）
CONDITION5_ENABLED: bool = False  # 是否启用条件5（低于MA8买入）
CONDITION6_ENABLED: bool = False  # 是否启用条件6（低于MA12买入）
CONDITION7_ENABLED: bool = False  # 是否启用条件7（14:54后低于MA4卖出）

# ========== 交易策略参数 ==========
BUY_BELOW_MA4_QUANTITY: int = 100  # 低于MA4买入数量
BUY_BELOW_MA8_QUANTITY: int = 100  # 低于MA8买入数量
BUY_BELOW_MA12_QUANTITY: int = 100  # 低于MA12买入数量