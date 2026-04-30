# service/conditions/cond8_sell_handler.py
# -*- coding: utf-8 -*-
"""条件8卖出逻辑处理，传递 config 到结果组装"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any
from domain.contexts.condition8 import Condition8Context
from config.strategy.config_objects import Condition8Config
from .cond8_quantity_calculator import _calculate_order_quantity
from .cond8_result_assembler import _assemble_return_data

logger = logging.getLogger(__name__)


def _handle_sell_logic(symbol: str, context: Condition8Context, current_price: float,
                       available_position: int, ref_price: float,
                       price_change: float, rise_threshold: float, decline_threshold: float,
                       stock_type: str, type_desc: str,
                       config: Condition8Config) -> Optional[Dict[str, Any]]:
    if available_position <= 0:
        logger.info('【持仓检查】%s 无可用持仓，跳过条件8卖出', symbol)
        return None
    if context.condition8_sell_triggered_for_current_ref:
        logger.info('【防重复】%s 当前基准价 %.4f 已触发过卖出挂单，不再重复触发', symbol, ref_price)
        return None

    calc_result = _calculate_order_quantity(context, symbol, current_price, ref_price, side="sell", config=config)
    final_quantity = calc_result["final_quantity"]
    base_quantity = calc_result["base_quantity"]
    actual_multiple = calc_result["actual_multiple"]
    hit_limit = calc_result["hit_limit"]
    skipped_grids = calc_result["skipped_grids"]

    logger.info('【条件8触发-%s】%s 上涨 %.2f%% >= 阈值 %.2f%%，基准价:%.4f 当前价:%.4f',
                type_desc, symbol, price_change * 100, rise_threshold * 100, ref_price, current_price)

    return _assemble_return_data(
        symbol=symbol, context=context, current_price=current_price, ref_price=ref_price,
        side="sell", quantity=final_quantity, base_quantity=base_quantity,
        actual_multiple=actual_multiple, skipped_grids=skipped_grids, hit_limit=hit_limit,
        rise_threshold=rise_threshold, decline_threshold=decline_threshold,
        stock_type=stock_type, type_desc=type_desc,
        reason=f'条件8(上涨触发卖出-{type_desc})',
        config=config,
    )