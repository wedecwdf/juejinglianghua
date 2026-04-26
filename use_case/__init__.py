# use_case/__init__.py
"""
用例编排层，被 GM 入口直接调用
"""
from .init_assets import build_tracking_symbols
from .handle_tick import handle_tick
from .handle_close import handle_market_close
from .health_check import (
    is_trading_day,
    is_in_trading_hours,
    should_sleep,
    should_wakeup,
    update_sleep_state,
    calculate_next_trading_start_time
)