# service/conditions/cond8_execution.py
# -*- coding: utf-8 -*-
"""
条件8：核心业务逻辑层、算法计算层、数据组装层。
配置从 config 参数获取。
"""
from __future__ import annotations
import logging
from typing import Dict, Any, Optional
from domain.day_data import DayData
from domain.contexts.condition8 import Condition8Context
from config.strategy.config_objects import Condition8Config
from .cond8_sell_handler import _handle_sell_logic
from .cond8_buy_handler import _handle_buy_logic

logger = logging.getLogger(__name__)


def _execute_trading_logic(day_data: DayData, context: Condition8Context, current_price: float,
                           available_position: int, ref_price: float,
                           price_change: float, rise_threshold: float,
                           decline_threshold: float, stock_type: str,
                           type_desc: str, config: Condition8Config) -> Optional[Dict[str, Any]]:
    symbol = day_data.symbol
    if price_change >= rise_threshold:
        return _handle_sell_logic(symbol, context, current_price, available_position,
                                  ref_price, price_change, rise_threshold, decline_threshold,
                                  stock_type, type_desc, config)
    elif price_change <= -decline_threshold:
        return _handle_buy_logic(symbol, context, current_price, ref_price, price_change,
                                 rise_threshold, decline_threshold, stock_type, type_desc, config)
    return None