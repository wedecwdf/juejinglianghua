# -*- coding: utf-8 -*-
"""
条件8：核心业务逻辑层、算法计算层、数据组装层

包含：
- _execute_trading_logic: 方向判断与分发
- _handle_sell_logic/_handle_buy_logic: 买卖方向业务逻辑（含防重复机制）
- _calculate_order_quantity: 倍数委托、跳过网格、数量计算
- _assemble_return_data: 返回字典构建与元数据填充
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import math

from domain.day_data import DayData
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


def _execute_trading_logic(day_data: DayData, current_price: float,
                           available_position: int, ref_price: float,
                           price_change: float, rise_threshold: float,
                           decline_threshold: float, stock_type: str,
                           type_desc: str) -> Optional[Dict[str, Any]]:
    """
    核心业务逻辑层：
    - 上涨/下跌方向判断
    - 防重复触发机制
    - 调用算法计算层进行数量计算
    - 调用数据组装层构建返回结果
    """
    # 上涨方向判断
    if price_change >= rise_threshold:
        return _handle_sell_logic(
            day_data=day_data,
            current_price=current_price,
            available_position=available_position,
            ref_price=ref_price,
            price_change=price_change,  # 传递 price_change
            rise_threshold=rise_threshold,
            decline_threshold=decline_threshold,
            stock_type=stock_type,
            type_desc=type_desc
        )

    # 下跌方向判断
    elif price_change <= -decline_threshold:
        return _handle_buy_logic(
            day_data=day_data,
            current_price=current_price,
            ref_price=ref_price,
            price_change=price_change,  # 传递 price_change
            rise_threshold=rise_threshold,
            decline_threshold=decline_threshold,
            stock_type=stock_type,
            type_desc=type_desc
        )

    return None


def _handle_sell_logic(day_data: DayData, current_price: float,
                       available_position: int, ref_price: float,
                       price_change: float,  # 【修复】添加 price_change 参数
                       rise_threshold: float, decline_threshold: float,
                       stock_type: str, type_desc: str) -> Optional[Dict[str, Any]]:
    """
    卖出方向核心业务逻辑：
    - 持仓检查
    - 防重复触发检查
    - 算法计算（倍数委托）
    - 数据组装
    """
    # 持仓检查
    if available_position <= 0:
        print(f'【持仓检查】无可用持仓，跳过条件8卖出')
        return None

    # 防重复触发机制
    if day_data.condition8_sell_triggered_for_current_ref:
        print(f'【防重复】{day_data.symbol} 当前基准价 {ref_price:.4f} '
              f'已触发过卖出挂单，不再重复触发')
        return None

    # 算法计算层：倍数委托计算
    calc_result = _calculate_order_quantity(
        day_data=day_data,
        current_price=current_price,
        ref_price=ref_price,
        side="sell",
        symbol=day_data.symbol
    )

    final_quantity = calc_result["final_quantity"]
    base_quantity = calc_result["base_quantity"]
    actual_multiple = calc_result["actual_multiple"]
    hit_limit = calc_result["hit_limit"]
    skipped_grids = calc_result["skipped_grids"]

    # 打印触发信息
    limit_msg = "【已达上限】" if hit_limit else ""
    if CONDITION8_MULTIPLE_ORDER_ENABLED and actual_multiple > 1:
        print(f'【倍数委托-卖出】{day_data.symbol} '
              f'上次触发价:{calc_result["last_trigger_price"]:.4f} 当前价:{current_price:.4f} '
              f'跳过网格:{skipped_grids} 基础数量:{base_quantity} '
              f'实际倍数:{actual_multiple} 最终数量:{final_quantity} {limit_msg}')

    print(
        f'【条件8触发-{type_desc}】{day_data.symbol} 上涨 {price_change * 100:.2f}% >= 阈值 {rise_threshold * 100:.2f}%，'
        f'基准价:{ref_price:.4f} 当前价:{current_price:.4f}')

    # 数据组装层
    return _assemble_return_data(
        day_data=day_data,
        current_price=current_price,
        ref_price=ref_price,
        side="sell",
        quantity=final_quantity,
        base_quantity=base_quantity,
        actual_multiple=actual_multiple,
        skipped_grids=skipped_grids,
        hit_limit=hit_limit,
        rise_threshold=rise_threshold,
        decline_threshold=decline_threshold,
        stock_type=stock_type,
        type_desc=type_desc,
        reason=f'条件8(上涨触发卖出-{type_desc})'
    )


def _handle_buy_logic(day_data: DayData, current_price: float,
                      ref_price: float,
                      price_change: float,  # 【修复】添加 price_change 参数
                      rise_threshold: float, decline_threshold: float,
                      stock_type: str, type_desc: str) -> Optional[Dict[str, Any]]:
    """
    买入方向核心业务逻辑：
    - 防重复触发检查
    - 算法计算（倍数委托）
    - 数据组装
    """
    # 防重复触发机制
    if day_data.condition8_buy_triggered_for_current_ref:
        print(f'【防重复】{day_data.symbol} 当前基准价 {ref_price:.4f} '
              f'已触发过买入挂单，不再重复触发')
        return None

    # 算法计算层：倍数委托计算
    calc_result = _calculate_order_quantity(
        day_data=day_data,
        current_price=current_price,
        ref_price=ref_price,
        side="buy",
        symbol=day_data.symbol
    )

    final_quantity = calc_result["final_quantity"]
    base_quantity = calc_result["base_quantity"]
    actual_multiple = calc_result["actual_multiple"]
    hit_limit = calc_result["hit_limit"]
    skipped_grids = calc_result["skipped_grids"]

    # 打印触发信息
    limit_msg = "【已达上限】" if hit_limit else ""
    if CONDITION8_MULTIPLE_ORDER_ENABLED and actual_multiple > 1:
        print(f'【倍数委托-买入】{day_data.symbol} '
              f'上次触发价:{calc_result["last_trigger_price"]:.4f} 当前价:{current_price:.4f} '
              f'跳过网格:{skipped_grids} 基础数量:{base_quantity} '
              f'实际倍数:{actual_multiple} 最终数量:{final_quantity} {limit_msg}')

    print(
        f'【条件8触发-{type_desc}】{day_data.symbol} 下跌 {abs(price_change) * 100:.2f}% >= 阈值 {decline_threshold * 100:.2f}%，'
        f'基准价:{ref_price:.4f} 当前价:{current_price:.4f}')

    # 数据组装层
    return _assemble_return_data(
        day_data=day_data,
        current_price=current_price,
        ref_price=ref_price,
        side="buy",
        quantity=final_quantity,
        base_quantity=base_quantity,
        actual_multiple=actual_multiple,
        skipped_grids=skipped_grids,
        hit_limit=hit_limit,
        rise_threshold=rise_threshold,
        decline_threshold=decline_threshold,
        stock_type=stock_type,
        type_desc=type_desc,
        reason=f'条件8(下跌触发买入-{type_desc})'
    )


def _calculate_order_quantity(day_data: DayData, current_price: float,
                              ref_price: float, side: str, symbol: str) -> Dict[str, Any]:
    """
    算法计算层：
    - 基础数量获取（买入/卖出配置）
    - 跳过网格数计算
    - 倍数委托数量计算
    - 数量上限约束（隐含在 _calculate_multiple_order_quantity 中）
    """
    # 基础数量获取
    if side == "sell":
        base_quantity = CONDITION8_SELL_QUANTITY.get(symbol, 100)
    else:
        base_quantity = CONDITION8_BUY_QUANTITY.get(symbol, 100)

    final_quantity = base_quantity
    actual_multiple = 1
    hit_limit = False
    skipped_grids = 0
    last_trigger_price_used = ref_price  # 默认使用ref_price，后续可能被覆盖

    # 倍数委托计算
    if CONDITION8_MULTIPLE_ORDER_ENABLED:
        last_trigger_price = day_data.condition8_last_trigger_price
        if last_trigger_price is None or last_trigger_price <= 0:
            last_trigger_price = ref_price

        last_trigger_price_used = last_trigger_price

        if last_trigger_price > 0:
            grid_interval = _get_grid_interval_percent(symbol)
            skipped_grids = _calculate_skipped_grids(
                last_trigger_price, current_price, grid_interval
            )

            if skipped_grids >= 1:
                final_quantity, actual_multiple, hit_limit = _calculate_multiple_order_quantity(
                    base_quantity, skipped_grids, CONDITION8_MAX_MULTIPLE_LIMIT
                )

    return {
        "final_quantity": final_quantity,
        "base_quantity": base_quantity,
        "actual_multiple": actual_multiple,
        "hit_limit": hit_limit,
        "skipped_grids": skipped_grids,
        "last_trigger_price": last_trigger_price_used,
    }


def _assemble_return_data(day_data: DayData, current_price: float,
                          ref_price: float, side: str, quantity: int,
                          base_quantity: int, actual_multiple: int,
                          skipped_grids: int, hit_limit: bool,
                          rise_threshold: float, decline_threshold: float,
                          stock_type: str, type_desc: str,
                          reason: str) -> Dict[str, Any]:
    """
    数据组装层：
    - 构建标准返回字典
    - 填充触发数据元数据（含倍数委托信息、阈值信息）
    - 保持与原函数返回结构100%一致
    """
    is_multiple_order = actual_multiple > 1

    # 获取用于 multiple_order_info 的 last_trigger_price
    last_trigger_for_meta = day_data.condition8_last_trigger_price
    if last_trigger_for_meta is None or last_trigger_for_meta <= 0:
        last_trigger_for_meta = day_data.base_price

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
            'pre_trigger_count': day_data.condition8_trade_times,
            'pre_ref_price': day_data.condition8_reference_price,
            'pre_trade_price': day_data.condition8_last_trade_price,
            'current_ref_price': ref_price,
            'is_multiple_order': is_multiple_order,
            'multiple_order_info': {
                'last_trigger_price': last_trigger_for_meta,
                'current_price': current_price,
                'skipped_grids': skipped_grids,
                'grid_interval_percent': _get_grid_interval_percent(day_data.symbol),
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