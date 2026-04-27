# service/conditions/cond8_execution.py
# -*- coding: utf-8 -*-
"""
条件8：核心业务逻辑层、算法计算层、数据组装层
所有 print 替换为 logger。
"""
from __future__ import annotations
import logging
from typing import Dict, Any, Optional
from domain.day_data import DayData
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


def _handle_sell_logic(symbol: str, context: Condition8Context, current_price: float,
                       available_position: int, ref_price: float,
                       price_change: float, rise_threshold: float, decline_threshold: float,
                       stock_type: str, type_desc: str) -> Optional[Dict[str, Any]]:
    if available_position <= 0:
        logger.info('【持仓检查】%s 无可用持仓，跳过条件8卖出', symbol)
        return None
    if context.condition8_sell_triggered_for_current_ref:
        logger.info('【防重复】%s 当前基准价 %.4f 已触发过卖出挂单，不再重复触发', symbol, ref_price)
        return None

    calc_result = _calculate_order_quantity(context, symbol, current_price, ref_price, side="sell")
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
        reason=f'条件8(上涨触发卖出-{type_desc})'
    )


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


def _assemble_return_data(symbol: str, context: Condition8Context, current_price: float,
                          ref_price: float, side: str, quantity: int,
                          base_quantity: int, actual_multiple: int,
                          skipped_grids: int, hit_limit: bool,
                          rise_threshold: float, decline_threshold: float,
                          stock_type: str, type_desc: str, reason: str) -> Dict[str, Any]:
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
                'grid_interval_percent': _get_grid_interval_percent(symbol),
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