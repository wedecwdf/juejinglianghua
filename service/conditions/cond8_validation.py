# service/conditions/cond8_validation.py
# -*- coding: utf-8 -*-
"""
条件8：系统状态检查层、业务规则校验层、数据获取层
所有 print 替换为 logger。
"""
from __future__ import annotations
import logging
import time
from typing import Dict, Any
from domain.contexts.condition8 import Condition8Context
from domain.stores import OrderLedger
from config.strategy import (
    CONDITION8_ENABLED,
    MAX_CONDITION8_TRADE_TIMES,
    CONDITION8_PRICE_BAND_ENABLED,
)
from .utils import (
    _get_condition8_thresholds,
    _get_stock_frequency_type,
)

logger = logging.getLogger(__name__)

def _check_system_state(order_ledger: OrderLedger, symbol: str, context: Condition8Context,
                        current_price: float) -> bool:
    if not CONDITION8_ENABLED:
        return False
    if order_ledger.is_cancelling(symbol):
        logger.info('【撤单保护】%s 正在撤单中，跳过条件8检查', symbol)
        return False

    if order_ledger.is_condition8_sleeping():
        if CONDITION8_PRICE_BAND_ENABLED:
            upper = context.condition8_upper_band
            lower = context.condition8_lower_band
            if upper is not None and lower is not None:
                if lower <= current_price <= upper:
                    context.condition8_sleeping = False
                    logger.info('【%s】【条件8】价格回到区间内，唤醒', symbol)
                else:
                    logger.info('【%s】【条件8】价格仍超出区间，保持休眠', symbol)
                    return False
            else:
                return False
        else:
            context.condition8_sleeping = False
    return True

def _validate_business_rules(context: Condition8Context, base_price: float,
                             current_price: float) -> bool:
    if context.condition8_trade_times >= MAX_CONDITION8_TRADE_TIMES:
        return False
    now_sec = time.time()
    last_trigger = context.condition8_last_trigger_time
    if last_trigger and (now_sec - last_trigger) < context.condition8_cooldown_period:
        return False
    if not context.condition8_sleeping:
        if CONDITION8_PRICE_BAND_ENABLED:
            upper = context.condition8_upper_band
            lower = context.condition8_lower_band
            if upper is not None and lower is not None:
                if current_price > upper or current_price < lower:
                    context.condition8_sleeping = True
                    logger.info(
                        '【条件8】基准价=%.4f 上轨=%.4f 下轨=%.4f 当前价=%.4f 价格超出区间，进入休眠',
                        base_price, upper, lower, current_price
                    )
                    return False
    return True

def _fetch_data(order_ledger: OrderLedger, symbol: str, context: Condition8Context,
                current_price: float) -> Dict[str, Any]:
    if order_ledger.pop_cancelled(symbol):
        ref_price = context.condition8_reference_price
        logger.info('【撤单重新判断】%s 使用基准价作为参考价: %.4f', symbol, ref_price)
    else:
        ref_price = context.condition8_reference_price
        if ref_price is None or ref_price <= 0:
            ref_price = 0.0

    rise_threshold, decline_threshold = _get_condition8_thresholds(symbol)
    stock_type = _get_stock_frequency_type(symbol)
    type_desc = "高频" if stock_type == 'high' else ("低频" if stock_type == 'low' else "默认")

    return {
        "ref_price": ref_price,
        "rise_threshold": rise_threshold,
        "decline_threshold": decline_threshold,
        "stock_type": stock_type,
        "type_desc": type_desc,
    }