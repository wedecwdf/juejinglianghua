# service/conditions/utils.py
# -*- coding: utf-8 -*-
"""
条件判断公共辅助函数
所有条件8相关阈值和间隔函数增加 config 参数，优先使用配置对象。
"""
from __future__ import annotations
from typing import Optional, Dict, Any, Tuple, TYPE_CHECKING

from config.strategy import (
    ENABLE_HIGH_LOW_FREQUENCY_CLASSIFICATION,
    HIGH_FREQUENCY_STOCKS,
    LOW_FREQUENCY_STOCKS,
)
# 向后兼容保留全局常量引用，但实际使用时若 config 提供则忽略
from config.strategy import CONDITION8_HIGH_FREQ_RISE_PERCENT, CONDITION8_HIGH_FREQ_DECLINE_PERCENT
from config.strategy import CONDITION8_LOW_FREQ_RISE_PERCENT, CONDITION8_LOW_FREQ_DECLINE_PERCENT
from config.strategy import CONDITION8_RISE_PERCENT, CONDITION8_DECLINE_PERCENT
from config.strategy import CONDITION8_GRID_INTERVAL_PERCENT
from config.strategy import CONDITION8_MAX_MULTIPLE_LIMIT

if TYPE_CHECKING:
    from config.strategy.config_objects import Condition2Config, Condition9Config


def _sell_qty_by_percent(available_position: int, percent: float) -> int:
    qty = int(available_position * percent)
    return (qty // 100) * 100


def _get_stock_frequency_type(symbol: str) -> str:
    if not ENABLE_HIGH_LOW_FREQUENCY_CLASSIFICATION:
        return 'default'
    if symbol in HIGH_FREQUENCY_STOCKS:
        return 'high'
    elif symbol in LOW_FREQUENCY_STOCKS:
        return 'low'
    else:
        return 'default'


def _get_condition8_thresholds(symbol: str, config: Optional['Condition8Config'] = None) -> Tuple[float, float]:
    if config is not None:
        stock_type = _get_stock_frequency_type(symbol)
        if stock_type == 'high':
            return config.high_freq_rise, config.high_freq_decline
        elif stock_type == 'low':
            return config.low_freq_rise, config.low_freq_decline
        else:
            return config.rise_percent, config.decline_percent
    else:
        stock_type = _get_stock_frequency_type(symbol)
        if stock_type == 'high':
            return CONDITION8_HIGH_FREQ_RISE_PERCENT, CONDITION8_HIGH_FREQ_DECLINE_PERCENT
        elif stock_type == 'low':
            return CONDITION8_LOW_FREQ_RISE_PERCENT, CONDITION8_LOW_FREQ_DECLINE_PERCENT
        else:
            return CONDITION8_RISE_PERCENT, CONDITION8_DECLINE_PERCENT


def _get_grid_interval_percent(symbol: str, config: Optional['Condition8Config'] = None) -> float:
    if config is not None:
        return config.grid_interval_percent
    return CONDITION8_GRID_INTERVAL_PERCENT


def _calculate_skipped_grids(last_trigger_price: float, current_price: float,
                             grid_interval_percent: float) -> int:
    if last_trigger_price <= 0 or grid_interval_percent <= 0:
        return 0
    price_change_abs = abs(current_price - last_trigger_price)
    single_grid_magnitude = last_trigger_price * grid_interval_percent
    if single_grid_magnitude <= 0:
        return 0
    skipped_grids = int(price_change_abs / single_grid_magnitude)
    return max(0, skipped_grids)


def _calculate_multiple_order_quantity(base_quantity: int, skipped_grids: int,
                                       max_multiple_limit: int) -> tuple:
    if skipped_grids <= 0:
        return base_quantity, 1, False
    actual_multiple = min(skipped_grids, max_multiple_limit)
    final_quantity = base_quantity * actual_multiple
    hit_limit = (skipped_grids >= max_multiple_limit)
    return final_quantity, actual_multiple, hit_limit


# ==================== 重构的动态止盈公共内核 ====================

def _check_dynamic_profit_core(
    context,
    increase: float,
    current_price: float,
    base_price: float,
    *,
    config: Optional[any] = None,
    condition_name: str,
    board_break_active: bool = False,
    priority_check_fn: Optional[callable] = None,
    get_triggered, set_triggered,
    get_high_price, set_high_price,
    get_profit_line, set_profit_line,
    get_sell_times, inc_sell_times,
) -> Optional[Dict[str, Any]]:

    if board_break_active or config is None or not config.enabled:
        return None
    current_sell_times = get_sell_times(context)
    if current_sell_times >= config.max_sell_times:
        return None
    if priority_check_fn and priority_check_fn():
        return None

    triggered = get_triggered(context)

    # 阶段一：启动监控
    if increase >= config.trigger_percent:
        if not triggered:
            set_triggered(context, True)
            set_high_price(context, current_price)
            set_profit_line(context, current_price * (1 - config.decline_percent))
            print(f'{getattr(context, "symbol", "?")}【{condition_name}动态止盈启动已启动】，'
                  f'初始基准价：{base_price:.4f} 当前涨跌幅：{increase*100:.2f}% '
                  f'初始止盈线：{get_profit_line(context):.4f}')
        return None

    if not triggered:
        return None

    # 阶段二：更新动态止盈线（创新高）
    current_high = get_high_price(context)
    if current_price > current_high:
        set_high_price(context, current_price)
        new_profit_line = current_price * (1 - config.decline_percent)
        set_profit_line(context, new_profit_line)
        print(f'【{condition_name}动态止盈】更新动态止盈线：{new_profit_line:.4f}')
        return None

    # 阶段三：检查跌破止盈线
    current_profit_line = get_profit_line(context)
    if current_price <= current_profit_line:
        dynamic_line_increase = (current_profit_line - base_price) / base_price if base_price > 0 else 0
        sell_percent = config.sell_percent_high if dynamic_line_increase >= config.dynamic_line_threshold \
                       else config.sell_percent_low
        return {
            'reason': f'{condition_name}动态止盈触发',
            'sell_price_offset': config.sell_price_offset,
            'sell_percent': sell_percent,
            'trigger_data': {
                'pre_trigger_state': True,
                'pre_high_price': current_high,
                'pre_profit_line': current_profit_line,
                'pre_sell_count': current_sell_times,
            }
        }
    return None