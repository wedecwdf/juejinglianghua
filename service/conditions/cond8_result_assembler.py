# service/conditions/cond8_result_assembler.py
# -*- coding: utf-8 -*-
"""条件8返回数据组装，通过 config 获取网格间隔"""
from __future__ import annotations
from typing import Dict, Any
from domain.contexts.condition8 import Condition8Context
from config.strategy.config_objects import Condition8Config
from .utils import _get_grid_interval_percent


def _assemble_return_data(symbol: str, context: Condition8Context, current_price: float,
                          ref_price: float, side: str, quantity: int,
                          base_quantity: int, actual_multiple: int,
                          skipped_grids: int, hit_limit: bool,
                          rise_threshold: float, decline_threshold: float,
                          stock_type: str, type_desc: str, reason: str,
                          config: Condition8Config) -> Dict[str, Any]:
    is_multiple_order = actual_multiple > 1
    last_trigger_for_meta = context.condition8_last_trigger_price
    if last_trigger_for_meta is None or last_trigger_for_meta <= 0:
        last_trigger_for_meta = ref_price

    return {
        'reason': reason,
        'side': side,
        'quantity': quantity,
        'base_quantity': base_quantity,
        'actual_multiple': actual_multiple,
        'skipped_grids': skipped_grids,
        'hit_limit': hit_limit,
        'price_offset': 0,
        'rise_threshold': rise_threshold,
        'decline_threshold': decline_threshold,
        'stock_type': stock_type,
        'trigger_data': {
            'pre_trigger_count': context.condition8_trade_times,
            'pre_ref_price': context.condition8_reference_price,
            'pre_trade_price': context.condition8_last_trade_price,
            'current_ref_price': ref_price,
            'is_multiple_order': is_multiple_order,
            'multiple_order_info': {
                'last_trigger_price': last_trigger_for_meta,
                'current_price': current_price,
                'skipped_grids': skipped_grids,
                'grid_interval_percent': _get_grid_interval_percent(symbol, config),
                'base_quantity': base_quantity,
                'actual_multiple': actual_multiple,
                'final_quantity': quantity,
                'hit_limit': hit_limit
            },
            'threshold_info': {
                'stock_type': stock_type,
                'rise_threshold_used': rise_threshold,
                'decline_threshold_used': decline_threshold,
                'price_change': (current_price - ref_price) / ref_price
            }
        }
    }