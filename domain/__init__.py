# domain/__init__.py
"""
业务实体层，无外部依赖
"""

from .day_data import DayData
from .base_price import (
    CallbackAdditionTask,
    calculate_trigger_prices,
    calculate_callback_buy_quantity,
)
from .board import BoardStatus, BoardBreakStatus, BoardCountData
from .constants import ConditionType, OrderSide, StockBoard

# 【新增导出】状态子对象（便于外部调试时按业务域查看状态，不破坏原有接口）
from .states import (
    MarketState, IndicatorState, Condition2State,
    Condition4To7State, Condition8State, Condition9State,
    MiscState, PyramidState, RecheckState, NextDayState,
)