# service/conditions/pyramid_profit.py
# -*- coding: utf-8 -*-
"""
金字塔止盈条件检查（独立机制），所有参数通过配置对象注入。
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.contexts.pyramid import PyramidContext
from config.strategy.config_objects import PyramidProfitConfig, Condition8Config


def check_pyramid_profit(symbol: str, context: PyramidContext, current_price: float,
                         available_position: int,
                         pyramid_config: PyramidProfitConfig,
                         condition8_config: Condition8Config) -> Optional[Dict[str, Any]]:
    if not pyramid_config.enabled or available_position <= 0:
        return None

    total_qty = pyramid_config.total_quantity.get(symbol, 0)
    if total_qty <= 0:
        return None

    custom_base = pyramid_config.user_base_price.get(symbol)
    if custom_base and custom_base > 0:
        base_price = custom_base
    else:
        base_price = context.pyramid_profit_base_price
    if base_price <= 0:
        return None

    price_increase = (current_price - base_price) / base_price

    if symbol in condition8_config.high_freq_stocks:
        levels = pyramid_config.high_freq_levels
        ratios = pyramid_config.high_freq_ratios
    elif symbol in condition8_config.low_freq_stocks:
        levels = pyramid_config.low_freq_levels
        ratios = pyramid_config.low_freq_ratios
    else:
        levels = pyramid_config.default_levels
        ratios = pyramid_config.default_ratios

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
        'sell_price_offset': pyramid_config.sell_price_offset,
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