# -*- coding: utf-8 -*-
"""
金字塔止盈策略配置模块（已从条件8独立）

机制说明：
- 完全独立于条件8动态基准价网格交易
- 拥有独立的基准价配置和状态管理
- 支持高频/低频/默认三套参数
- 支持用户自定义基准价覆盖
"""

from typing import Dict, List

# ========== 金字塔止盈总开关 ==========
PYRAMID_PROFIT_ENABLED: bool = True  # 是否启用金字塔止盈

# ========== 基准价配置 ==========
# 用户自定义基准价（优先级最高）
PYRAMID_USER_BASE_PRICE: Dict[str, float] = {
    'SZSE.002793': 5.80,
    'SHSE.560660': 1000,
}

# ========== 分级止盈参数 ==========
# 高频股票参数
PYRAMID_HIGH_FREQUENCY: Dict[str, List[float]] = {
    'levels': [0.035, 0.045, 0.065],  # 三级止盈阈值（涨幅）
    'ratios': [0.2, 0.3, 0.5]         # 各级别卖出比例
}

# 低频股票参数
PYRAMID_LOW_FREQUENCY: Dict[str, List[float]] = {
    'levels': [0.05, 0.07, 0.1],
    'ratios': [0.1, 0.2, 0.7]
}

# 默认参数
PYRAMID_DEFAULT: Dict[str, List[float]] = {
    'levels': [0.02, 0.03, 0.039],
    'ratios': [0.1, 0.1, 0.1]
}

# ========== 交易参数 ==========
PYRAMID_PROFIT_SELL_PRICE_OFFSET: float = 0.01  # 卖出价格偏移

# ========== 股票分类配置（与条件8共用分类，但独立判断） ==========
# 注意：此处引用条件8的股票分类，但金字塔止盈独立启用/禁用
from config.strategy.condition8 import HIGH_FREQUENCY_STOCKS, LOW_FREQUENCY_STOCKS

# ========== 每只股票的金字塔止盈总数量配置 ==========
# 与条件8的持仓管理完全独立
PYRAMID_TOTAL_QUANTITY: Dict[str, int] = {}  # 默认空，初始化时填充

# 高频/低频默认数量（如果PYRAMID_TOTAL_QUANTITY未指定）
PYRAMID_HIGH_FREQ_QUANTITY: int = 10000
PYRAMID_LOW_FREQ_QUANTITY: int = 1000
PYRAMID_DEFAULT_QUANTITY: int = 1000

# 初始化股票数量映射（保持向后兼容的数据结构）
def _initialize_pyramid_quantities():
    """初始化高频/低频股票的金字塔止盈数量"""
    for stock in HIGH_FREQUENCY_STOCKS:
        if stock not in PYRAMID_TOTAL_QUANTITY:
            PYRAMID_TOTAL_QUANTITY[stock] = PYRAMID_HIGH_FREQ_QUANTITY
    for stock in LOW_FREQUENCY_STOCKS:
        if stock not in PYRAMID_TOTAL_QUANTITY:
            PYRAMID_TOTAL_QUANTITY[stock] = PYRAMID_LOW_FREQ_QUANTITY

# 模块导入时自动初始化
_initialize_pyramid_quantities()