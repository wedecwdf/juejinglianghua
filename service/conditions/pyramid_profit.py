# service/conditions/pyramid_profit.py
# -*- coding: utf-8 -*-
"""金字塔止盈条件检查（独立机制）"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.contexts.pyramid import PyramidContext
from config.strategy import (
    PYRAMID_PROFIT_ENABLED,
    PYRAMID_USER_BASE_PRICE,
    PYRAMID_HIGH_FREQUENCY,
    PYRAMID_LOW_FREQUENCY,
    PYRAMID_DEFAULT,
    PYRAMID_TOTAL_QUANTITY,
    PYRAMID_PROFIT_SELL_PRICE_OFFSET,
    HIGH_FREQUENCY_STOCKS,
    LOW_FREQUENCY_STOCKS,
)

def check_pyramid_profit(symbol: str, context: PyramidContext, current_price: float,
                         available_position: int) -> Optional[Dict[str, Any]]:
    if not PYRAMID_PROFIT_ENABLED or available_position <= 0:
        return None

    total_qty = PYRAMID_TOTAL_QUANTITY.get(symbol, 0)
    if total_qty <= 0:
        return None

    # 确定基准价
    custom_base = PYRAMID_USER_BASE_PRICE.get(symbol)
    if custom_base and custom_base > 0:
        base_price = custom_base
    else:
        base_price = context.pyramid_profit_base_price
    if base_price <= 0:
        return None

    price_increase = (current_price - base_price) / base_price
    if symbol in HIGH_FREQUENCY_STOCKS:
        params = PYRAMID_HIGH_FREQUENCY
    elif symbol in LOW_FREQUENCY_STOCKS:
        params = PYRAMID_LOW_FREQUENCY
    else:
        params = PYRAMID_DEFAULT

    levels = params['levels']
    ratios = params['ratios']
    status = context.pyramid_profit_status

    triggered_level = -1
    for i, level in enumerate(levels):
        if price_increase >= level and not status[i]:
            triggered_level = i
            break

    if triggered_level < 0:
        return None

    sell_qty = int(total_qty * ratios[triggered_level])
    sell_qty = (sell_qty // 100) * 100
    sell_qty = min(sell_qty, available_position)
    if sell_qty <= 0:
        return None

    return {
        'reason': f'金字塔止盈第{triggered_level + 1}级（独立机制）',
        'sell_price_offset': PYRAMID_PROFIT_SELL_PRICE_OFFSET,
        'quantity': sell_qty,
        'trigger_data': {
            'pyramid_level': triggered_level,
            'pyramid_status': status.copy(),
            'pyramid_total_quantity': total_qty,
            'pyramid_levels': levels.copy(),
            'pyramid_ratios': ratios.copy(),
            'base_price_used': base_price,
            'price_increase': price_increase,
            'is_independent': True
        }
    }