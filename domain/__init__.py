# domain/__init__.py
"""
业务实体层，无外部依赖
移除旧的 states 导入，保留核心实体和上下文导出。
"""
from .day_data import DayData
from .base_price import (
    CallbackAdditionTask,
    calculate_trigger_prices,
    calculate_callback_buy_quantity,
)
from .board import BoardStatus, BoardBreakStatus, BoardCountData
from .constants import ConditionType, OrderSide, StockBoard

# 不再有全局的 MarketState 等，已由条件上下文替代