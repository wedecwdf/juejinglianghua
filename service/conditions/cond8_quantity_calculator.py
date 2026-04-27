# service/conditions/cond8_quantity_calculator.py
# -*- coding: utf-8 -*-
"""条件8数量计算（基础数量、倍数委托、跳过网格）"""
from __future__ import annotations
import logging
from typing import Dict, Any
from domain.contexts.condition8 import Condition8Context
from config.strategy import (
    CONDITION8_SELL_QUANTITY,
    CONDITION8_BUY_QUANTITY,
    CONDITION8_MULTIPLE_ORDER_ENABLED,
    CONDITION8_MAX_MULTIPLE_LIMIT,
)
from .utils import (
    _get_grid_interval_percent,
    _calculate_skipped_grids,
    _calculate_multiple_order_quantity,
)

logger = logging.getLogger(__name__)


def _calculate_order_quantity(context: Condition8Context, symbol: str, current_price: float,
                              ref_price: float, side: str) -> Dict[str, Any]:
    if side == "sell":
        base_quantity = CONDITION8_SELL_QUANTITY.get(symbol, 100)
    else:
        base_quantity = CONDITION8_BUY_QUANTITY.get(symbol, 100)

    final_quantity = base_quantity
    actual_multiple = 1
    hit_limit = False
    skipped_grids = 0
    last_trigger_price_used = ref_price

    if CONDITION8_MULTIPLE_ORDER_ENABLED:
        last_trigger_price = context.condition8_last_trigger_price
        if last_trigger_price is None or last_trigger_price <= 0:
            last_trigger_price = ref_price
        last_trigger_price_used = last_trigger_price
        if last_trigger_price > 0:
            grid_interval = _get_grid_interval_percent(symbol)
            skipped_grids = _calculate_skipped_grids(last_trigger_price, current_price, grid_interval)
            if skipped_grids >= 1:
                final_quantity, actual_multiple, hit_limit = _calculate_multiple_order_quantity(
                    base_quantity, skipped_grids, CONDITION8_MAX_MULTIPLE_LIMIT
                )

    if CONDITION8_MULTIPLE_ORDER_ENABLED and actual_multiple > 1:
        limit_msg = "【已达上限】" if hit_limit else ""
        logger.info(
            '【倍数委托-%s】%s 上次触发价:%.4f 当前价:%.4f 跳过网格:%d 基础数量:%d 实际倍数:%d 最终数量:%d %s',
            side, symbol, last_trigger_price_used, current_price, skipped_grids, base_quantity,
            actual_multiple, final_quantity, limit_msg
        )

    return {
        "final_quantity": final_quantity,
        "base_quantity": base_quantity,
        "actual_multiple": actual_multiple,
        "hit_limit": hit_limit,
        "skipped_grids": skipped_grids,
        "last_trigger_price": last_trigger_price_used,
    }