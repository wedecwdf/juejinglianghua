# adapter/__init__.py
"""
与 GM 事件直接对接的薄层
"""
from .context_wrapper import ContextWrapper
from .event_handler import on_tick, on_error, on_backtest_finished
from .main import run_strategy

