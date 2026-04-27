# service/conditions/cond8_buy_handler.py
# -*- coding: utf-8 -*-
"""条件8买入逻辑处理"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any
from domain.contexts.condition8 import Condition8Context
from .cond8_quantity_calculator import _calculate_order_quantity
from .cond8_result_assembler import _assemble_return_data

logger = logging.getLogger(__name__)


def _handle_buy_logic(symbol: str, context: Condition8Context, current_price: float,
                      ref_price: float, price_change: float, rise_threshold: float,
                      decline_threshold: float, stock_type: str, type_desc: str) -> Optional[Dict[str, Any]]:
    if context.condition8_buy_triggered_for_current_ref:
        logger.info('【防重复】%s 当前基准价 %.4f 已触发过买入挂单，不再重复触发', symbol, ref_price)
        return None

    calc_result = _calculate_order_quantity(context, symbol, current_price, ref_price, side="buy")
    final_quantity = calc_result["final_quantity"]
    base_quantity = calc_result["base_quantity"]
    actual_multiple = calc_result["actual_multiple"]
    hit_limit = calc_result["hit_limit"]
    skipped_grids = calc_result["skipped_grids"]

    logger.info('【条件8触发-%s】%s 下跌 %.2f%% >= 阈值 %.2f%%，基准价:%.4f 当前价:%.4f',
                type_desc, symbol, abs(price_change) * 100, decline_threshold * 100, ref_price, current_price)

    return _assemble_return_data(
        symbol=symbol, context=context, current_price=current_price, ref_price=ref_price,
        side="buy", quantity=final_quantity, base_quantity=base_quantity,
        actual_multiple=actual_multiple, skipped_grids=skipped_grids, hit_limit=hit_limit,
        rise_threshold=rise_threshold, decline_threshold=decline_threshold,
        stock_type=stock_type, type_desc=type_desc,
        reason=f'条件8(下跌触发买入-{type_desc})'
    )