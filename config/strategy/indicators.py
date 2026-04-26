# -*- coding: utf-8 -*-
"""
技术指标参数配置模块

包含：MA、CCI、MACD计算周期及阈值
"""

from typing import List  # 【修复】添加这行

# ========== 技术指标参数 ==========
MA_PERIODS: List[int] = [4, 8, 12, 50, 120]  # 均线计算周期
CCI_PERIOD: int = 14  # CCI计算周期
MACD_FAST: int = 12  # MACD快线周期
MACD_SLOW: int = 26  # MACD慢线周期
MACD_SIGNAL: int = 9  # MACD信号线周期
MACD_MIN_PERIOD: int = MACD_SLOW + MACD_SIGNAL - 1  # MACD最小计算周期
CCI_UPPER_LIMIT: int = 100  # CCI上限
CCI_LOWER_LIMIT: int = -100  # CCI下限

# 最大历史数据天数计算
import os
MAX_HISTORY_DAYS: int = max(MA_PERIODS + [CCI_PERIOD, MACD_MIN_PERIOD]) * 3  # 最大历史数据天数