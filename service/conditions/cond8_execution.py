# service/conditions/cond8_execution.py
# -*- coding: utf-8 -*-
"""
条件8：核心执行流转模块，整合卖出/买入/数量和组装逻辑。
"""
from __future__ import annotations
import logging
from typing import Dict, Any, Optional
from domain.day_data import DayData
from domain.contexts.condition8 import Condition8Context
from .cond8_sell_handler import _handle_sell_logic
from .cond8_buy_handler import _handle_buy_logic

logger = logging.getLogger(__name__)


def _execute_trading_logic(day_data: DayData, context: Condition8Context, current_price: float,
                           available_position: int, ref_price: float,
                           price_change: float, rise_threshold: float,
                           decline_threshold: float, stock_type: str,
                           type_desc: str) -> Optional[Dict[str, Any]]:
    symbol = day_data.symbol
    if price_change >= rise_threshold:
        return _handle_sell_logic(symbol, context, current_price, available_position,
                                  ref_price, price_change, rise_threshold, decline_threshold,
                                  stock_type, type_desc)
    elif price_change <= -decline_threshold:
        return _handle_buy_logic(symbol, context, current_price, ref_price, price_change,
                                 rise_threshold, decline_threshold, stock_type, type_desc)
    return None