# service/conditions/cond8_validation.py
# -*- coding: utf-8 -*-
"""
条件8：系统状态检查层、业务规则校验层、数据获取层
修改：从 domain.stores 统一导入 OrderLedger
"""
from __future__ import annotations
from typing import Dict, Any
import time
from domain.day_data import DayData
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

def _check_system_state(order_ledger: OrderLedger, day_data: DayData,
                        current_price: float) -> bool:
    if not CONDITION8_ENABLED:
        return False

    if order_ledger.is_cancelling(day_data.symbol):
        print(f'【撤单保护】{day_data.symbol} 正在撤单中，跳过条件8检查')
        return False

    if order_ledger.is_condition8_sleeping():
        if CONDITION8_PRICE_BAND_ENABLED:
            upper = day_data.condition8_upper_band
            lower = day_data.condition8_lower_band
            if upper is not None and lower is not None:
                if lower <= current_price <= upper:
                    day_data.condition8_sleeping = False
                    print(f'【{day_data.symbol}】【条件8】价格回到区间内，唤醒')
                else:
                    print(f'【{day_data.symbol}】【条件8】价格仍超出区间，保持休眠')
                    return False
            else:
                return False
        else:
            day_data.condition8_sleeping = False
    return True

def _validate_business_rules(day_data: DayData,
                             current_price: float) -> bool:
    if day_data.condition8_trade_times >= MAX_CONDITION8_TRADE_TIMES:
        return False

    now_sec = time.time()
    last_trigger = day_data.condition8_last_trigger_time
    if last_trigger and (now_sec - last_trigger) < day_data.condition8_cooldown_period:
        return False

    if not day_data.condition8_sleeping:
        if CONDITION8_PRICE_BAND_ENABLED:
            upper = day_data.condition8_upper_band
            lower = day_data.condition8_lower_band
            if upper is not None and lower is not None:
                if current_price > upper or current_price < lower:
                    day_data.condition8_sleeping = True
                    print(f'【{day_data.symbol}】【条件8】基准价={day_data.base_price:.4f} '
                          f'上轨={upper:.4f} 下轨={lower:.4f} 当前价={current_price:.4f} '
                          f'价格超出区间，进入休眠')
                    return False
    return True

def _fetch_data(order_ledger: OrderLedger, day_data: DayData,
                current_price: float) -> Dict[str, Any]:
    if order_ledger.pop_cancelled(day_data.symbol):
        ref_price = day_data.base_price
        print(f'【撤单重新判断】{day_data.symbol} 使用基准价作为参考价: {ref_price:.4f}')
    else:
        ref_price = day_data.condition8_reference_price
        if ref_price is None or ref_price <= 0:
            ref_price = day_data.base_price

    rise_threshold, decline_threshold = _get_condition8_thresholds(day_data.symbol)
    stock_type = _get_stock_frequency_type(day_data.symbol)
    type_desc = "高频" if stock_type == 'high' else ("低频" if stock_type == 'low' else "默认")

    return {
        "ref_price": ref_price,
        "rise_threshold": rise_threshold,
        "decline_threshold": decline_threshold,
        "stock_type": stock_type,
        "type_desc": type_desc,
    }