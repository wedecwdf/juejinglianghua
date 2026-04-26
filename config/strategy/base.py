# -*- coding: utf-8 -*-
"""
基础策略配置模块

包含：股票代码订阅、系统参数、行情订阅、自动撤单、休眠开关
"""

import os
from typing import List, Dict

# ========== 股票代码订阅模式配置 ==========
SYMBOLS_SOURCE: str = "position"  # 股票代码来源：position-持仓，manual-手动，both-两者
MANUAL_SYMBOLS_ENABLED: bool = True  # 是否启用手动输入股票代码
MANUAL_SYMBOLS: List[str] = [  # 手动输入的股票代码列表
    'SZSE.002842',
    'SZSE.002513',
]

# ========== 系统参数 ==========
MAX_TOTAL_SELL_TIMES: int = 100  # 最大总卖出次数
REFRESH_INTERVAL: int = 3  # 行情刷新间隔（秒）
VOLUME_BAR_COUNT: int = 10  # 成交量柱数量
MACD_HIST_BAR_COUNT: int = 10  # MACD柱数量

# ========== 行情订阅配置 ==========
SUBSCRIBE_MODE: str = "parallel"  # 订阅模式：parallel-并行，sequential-顺序
TICK_SUBSCRIBE_COUNT: int = 1  # tick订阅数量
TICK_SUBSCRIBE_WAIT_GROUP: bool = False  # 是否等待组订阅完成
TICK_SUBSCRIBE_FIELDS: str = "symbol,created_at,price,cum_volume"  # tick订阅字段
BATCH_SUBSCRIBE_MAX_SYMBOLS: int = 50  # 批量订阅最大股票数量

# 动态跟踪的股票列表（将在初始化时设置）
symbols_to_track: List[str] = []

# ========== 自动撤单配置 ==========
AUTO_CANCEL_ENABLED: bool = True  # 是否启用自动撤单
AUTO_CANCEL_TIMEOUT: int = 5  # 自动撤单超时时间（秒）
AUTO_CANCEL_CHECK_INTERVAL: int = 5  # 自动撤单检查间隔（秒）

# 条件8独立撤单超时（秒）
CONDITION8_CANCEL_TIMEOUT: int = 6000  # 条件8挂单最大存活时间（秒）

# ========== 休眠模式开关 ==========
ENABLE_SLEEP_MODE: bool = True  # 是否启用休眠模式

# ========== 交易日检查配置 ==========
MAX_TRADING_DAY_CHECK_RETRY: int = 3  # 交易日检查最大重试次数