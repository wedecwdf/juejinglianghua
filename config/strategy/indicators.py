# config/strategy/indicators.py
# -*- coding: utf-8 -*-
"""技术指标参数（不属于策略业务配置）"""
from typing import List

MA_PERIODS: List[int] = [4, 8, 12, 50, 120]
CCI_PERIOD: int = 14
MACD_FAST: int = 12
MACD_SLOW: int = 26
MACD_SIGNAL: int = 9
MACD_MIN_PERIOD: int = MACD_SLOW + MACD_SIGNAL - 1
CCI_UPPER_LIMIT: int = 100
CCI_LOWER_LIMIT: int = -100
VOLUME_BAR_COUNT: int = 10
MACD_HIST_BAR_COUNT: int = 10

import os
MAX_HISTORY_DAYS: int = max(MA_PERIODS + [CCI_PERIOD, MACD_MIN_PERIOD]) * 3