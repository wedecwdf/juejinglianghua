# repository/__init__.py
"""
持久化网关（读写 JSON + GM API）
"""

from .state_gateway import StateGateway
from .gm_data_source import (
    load_history_data,
    get_available_position,
    # get_account_data,      # ← 这一行已删除
    get_cash,
    get_position,
    get_orders,
    order_cancel,
    order_volume,
    get_trading_dates,
    history
)
from .mail_sender import send_email