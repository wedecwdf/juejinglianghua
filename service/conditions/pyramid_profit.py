# -*- coding: utf-8 -*-
"""
金字塔止盈条件检查（已从条件8完全独立）

机制说明：
1. 使用独立的基准价（pyramid_profit_base_price），不再依赖条件8的基准价
2. 使用独立的配置参数（PYRAMID_*），不再依赖条件8的配置
3. 使用独立的状态字段（pyramid_profit_status），不再依赖条件8的状态
4. 支持用户自定义基准价覆盖
"""

from __future__ import annotations
from typing import Optional, Dict, Any

from domain.day_data import DayData
from repository.state_gateway import StateGateway

# 导入独立的金字塔止盈配置
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


def check_pyramid_profit(day_data: DayData, current_price: float,
                         available_position: int) -> Optional[Dict[str, Any]]:
    """
    检查金字塔止盈触发条件（完全独立版）

    独立性保证：
    - 基准价：使用 day_data.pyramid_profit_base_price（独立字段）
    - 配置：使用 PYRAMID_* 系列配置（独立配置）
    - 状态：使用 day_data.pyramid_profit_status（独立状态）

    Args:
        day_data: 日线数据（包含独立的金字塔止盈状态）
        current_price: 当前价格
        available_position: 可用持仓

    Returns:
        触发时返回卖出指令字典，否则返回None
    """
    # 总开关检查
    if not PYRAMID_PROFIT_ENABLED:
        return None

    # 持仓检查
    if available_position <= 0:
        return None

    # 获取该股票的金字塔止盈总数量（独立配置）
    total_qty = PYRAMID_TOTAL_QUANTITY.get(day_data.symbol, 0)
    if total_qty <= 0:
        return None

    # 确定基准价（优先级：用户自定义 > 独立基准价字段 > 开盘价）
    custom_base = PYRAMID_USER_BASE_PRICE.get(day_data.symbol)
    if custom_base and custom_base > 0:
        base_price = custom_base
    elif day_data.pyramid_profit_base_price and day_data.pyramid_profit_base_price > 0:
        base_price = day_data.pyramid_profit_base_price
    else:
        base_price = day_data.base_price  # 最终降级使用基础开盘价

    if base_price <= 0:
        return None

    # 计算涨幅
    price_increase = (current_price - base_price) / base_price

    # 获取该股票的分级参数（高频/低频/默认）
    if day_data.symbol in HIGH_FREQUENCY_STOCKS:
        params = PYRAMID_HIGH_FREQUENCY
    elif day_data.symbol in LOW_FREQUENCY_STOCKS:
        params = PYRAMID_LOW_FREQUENCY
    else:
        params = PYRAMID_DEFAULT

    levels = params['levels']  # 如 [0.035, 0.045, 0.065]
    ratios = params['ratios']  # 如 [0.2, 0.3, 0.5]
    status = day_data.pyramid_profit_status  # 独立状态字段 [False, False, False]

    # 检查是否触发某一级止盈
    triggered_level = -1
    for i, level in enumerate(levels):
        if price_increase >= level and not status[i]:
            triggered_level = i
            break

    if triggered_level < 0:
        return None

    # 计算卖出数量
    sell_qty = int(total_qty * ratios[triggered_level])
    sell_qty = (sell_qty // 100) * 100  # 取整到100股
    sell_qty = min(sell_qty, available_position)  # 不超过可用持仓

    if sell_qty <= 0:
        return None

    return {
        'reason': f'金字塔止盈第{triggered_level + 1}级（独立机制）',
        'sell_price_offset': PYRAMID_PROFIT_SELL_PRICE_OFFSET,
        'quantity': sell_qty,
        'trigger_data': {
            'pyramid_level': triggered_level,
            'pyramid_status': status.copy(),  # 独立状态快照
            'pyramid_total_quantity': total_qty,
            'pyramid_levels': levels.copy(),
            'pyramid_ratios': ratios.copy(),
            'base_price_used': base_price,  # 记录实际使用的基准价
            'price_increase': price_increase,
            'is_independent': True  # 标记为独立机制触发
        }
    }