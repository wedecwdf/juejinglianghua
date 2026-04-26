# -*- coding: utf-8 -*-
"""
条件判断公共辅助函数
"""
from __future__ import annotations
from typing import Tuple, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from domain.day_data import DayData

from config.strategy import (
    ENABLE_HIGH_LOW_FREQUENCY_CLASSIFICATION,
    HIGH_FREQUENCY_STOCKS,
    LOW_FREQUENCY_STOCKS,
    CONDITION8_HIGH_FREQ_RISE_PERCENT,
    CONDITION8_HIGH_FREQ_DECLINE_PERCENT,
    CONDITION8_LOW_FREQ_RISE_PERCENT,
    CONDITION8_LOW_FREQ_DECLINE_PERCENT,
    CONDITION8_RISE_PERCENT,
    CONDITION8_DECLINE_PERCENT,
    CONDITION8_GRID_INTERVAL_PERCENT,
    CONDITION8_HIGH_FREQ_GRID_INTERVAL,
    CONDITION8_LOW_FREQ_GRID_INTERVAL,
    CONDITION8_MAX_MULTIPLE_LIMIT,
)


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


def _get_condition8_thresholds(symbol: str) -> Tuple[float, float]:
    stock_type = _get_stock_frequency_type(symbol)
    if stock_type == 'high':
        return CONDITION8_HIGH_FREQ_RISE_PERCENT, CONDITION8_HIGH_FREQ_DECLINE_PERCENT
    elif stock_type == 'low':
        return CONDITION8_LOW_FREQ_RISE_PERCENT, CONDITION8_LOW_FREQ_DECLINE_PERCENT
    else:
        return CONDITION8_RISE_PERCENT, CONDITION8_DECLINE_PERCENT


def _get_grid_interval_percent(symbol: str) -> float:
    if not ENABLE_HIGH_LOW_FREQUENCY_CLASSIFICATION:
        return CONDITION8_GRID_INTERVAL_PERCENT
    if symbol in HIGH_FREQUENCY_STOCKS:
        return CONDITION8_HIGH_FREQ_GRID_INTERVAL
    elif symbol in LOW_FREQUENCY_STOCKS:
        return CONDITION8_LOW_FREQ_GRID_INTERVAL
    else:
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
                                       max_multiple_limit: int) -> tuple[int, int, bool]:
    if skipped_grids <= 0:
        return base_quantity, 1, False
    actual_multiple = min(skipped_grids, max_multiple_limit)
    final_quantity = base_quantity * actual_multiple
    hit_limit = (skipped_grids >= max_multiple_limit)
    return final_quantity, actual_multiple, hit_limit


# ==================== 新增：动态止盈公共内核 ====================

def _check_dynamic_profit_core(
        day_data: 'DayData',
        increase: float,
        current_price: float,
        base_price: float,
        *,
        enabled: bool,
        max_sell_times: int,
        trigger_percent: float,
        decline_percent: float,
        sell_price_offset: float,
        dynamic_line_threshold: float,
        sell_percent_high: float,
        sell_percent_low: float,
        triggered_flag_attr: str,  # e.g., 'dynamic_profit_triggered'
        high_price_attr: str,  # e.g., 'dynamic_profit_high_price'
        profit_line_attr: str,  # e.g., 'dynamic_profit_line'
        sell_times_attr: str,  # e.g., 'dynamic_profit_sell_times'
        condition_name: str,  # e.g., '条件2'
        board_break_active: bool = False,
        priority_check_fn: Optional[callable] = None  # 优先级覆盖检查函数
) -> Optional[Dict[str, Any]]:
    """
    动态止盈公共内核函数

     Args:
        priority_check_fn: 可选的优先级检查回调，返回True表示应跳过本条件
    """
    if board_break_active:
        return None

    if not enabled:
        return None

    current_sell_times = getattr(day_data, sell_times_attr, 0)
    if current_sell_times >= max_sell_times:
        return None

    # 优先级覆盖检查（如条件9检查条件2是否已触发）
    if priority_check_fn and priority_check_fn():
        return None

    triggered = getattr(day_data, triggered_flag_attr, False)

    # 阶段一：启动动态止盈监控
    if increase >= trigger_percent:
        if not triggered:
            setattr(day_data, triggered_flag_attr, True)
            setattr(day_data, high_price_attr, current_price)
            setattr(day_data, profit_line_attr, current_price * (1 - decline_percent))
            print(f'{day_data.symbol}【{condition_name}动态止盈启动已启动】，初始基准价：{base_price:.4f} '
                  f'当前涨跌幅：{increase * 100:.2f}% '
                  f'初始止盈线：{getattr(day_data, profit_line_attr):.4f}')
        return None

    if not triggered:
        return None

    # 阶段二：更新动态止盈线（创新高）
    current_high = getattr(day_data, high_price_attr, float('-inf'))
    if current_price > current_high:
        setattr(day_data, high_price_attr, current_price)
        new_profit_line = current_price * (1 - decline_percent)
        setattr(day_data, profit_line_attr, new_profit_line)
        print(f'{day_data.symbol}【{condition_name}动态止盈】更新动态止盈线：{new_profit_line:.4f}')
        return None

    # 阶段三：检查是否跌破止盈线
    current_profit_line = getattr(day_data, profit_line_attr, float('-inf'))
    if current_price <= current_profit_line:
        dynamic_line_increase = (current_profit_line - base_price) / base_price if base_price > 0 else 0
        sell_percent = sell_percent_high if dynamic_line_increase >= dynamic_line_threshold else sell_percent_low

        return {
            'reason': f'{condition_name}动态止盈触发',
            'sell_price_offset': sell_price_offset,
            'sell_percent': sell_percent,
            'trigger_data': {
                'pre_trigger_state': True,
                'pre_high_price': current_high,
                'pre_profit_line': current_profit_line,
                'pre_sell_count': current_sell_times,
                'pre_total_sell': getattr(day_data, 'total_sell_times', 0)
            }
        }

    return None