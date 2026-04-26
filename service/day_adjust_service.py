# service/day_adjust_service.py
# -*- coding: utf-8 -*-
"""
次日固定止损机制，无 GM 依赖
"""
from __future__ import annotations
from typing import Any, Dict
from domain.day_data import DayData
from config.strategy import (
    DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED,
    DYNAMIC_PROFIT_NEXT_DAY_STOP_LOSS_PRICE_OFFSET,
    DYNAMIC_PROFIT_NEXT_DAY_MAX_SELL_RATIO,
    DYNAMIC_PROFIT_NEXT_DAY_MAX_DAYS,
    CONDITION2_DYNAMIC_LINE_THRESHOLD, CONDITION2_SELL_PERCENT_HIGH, CONDITION2_SELL_PERCENT_LOW,
    CONDITION9_DYNAMIC_LINE_THRESHOLD, CONDITION9_SELL_PERCENT_HIGH, CONDITION9_SELL_PERCENT_LOW
)

def initialize_next_day_adjustment(day_data: DayData, prev_close_price: float) -> None:
    if not DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED:
        return
    adj = day_data.dynamic_profit_next_day_adjustment
    c2_activated = adj.get("condition2_activated", False)
    c9_activated = adj.get("condition9_activated", False)
    if not (c2_activated or c9_activated):
        adj["enabled"] = False
        return

    c2_high = adj.get("condition2_high_line", -float("inf"))
    c9_high = adj.get("condition9_high_line", -float("inf"))
    stop_loss_price = max(c2_high, c9_high)
    if stop_loss_price <= 0:
        adj["enabled"] = False
        return

    sell_ratio = 0.0
    if c2_activated:
        inc = (c2_high - prev_close_price) / prev_close_price
        sell_ratio += (CONDITION2_SELL_PERCENT_HIGH if inc >= CONDITION2_DYNAMIC_LINE_THRESHOLD
                       else CONDITION2_SELL_PERCENT_LOW)
    if c9_activated:
        inc = (c9_high - prev_close_price) / prev_close_price
        sell_ratio += (CONDITION9_SELL_PERCENT_HIGH if inc >= CONDITION9_DYNAMIC_LINE_THRESHOLD
                       else CONDITION9_SELL_PERCENT_LOW)
    sell_ratio = min(sell_ratio, DYNAMIC_PROFIT_NEXT_DAY_MAX_SELL_RATIO)

    days_count = adj.get("days_count", 0) + 1
    if days_count > DYNAMIC_PROFIT_NEXT_DAY_MAX_DAYS:
        adj["enabled"] = False
        print(f"【次日调整机制】达到最大延续天数{DYNAMIC_PROFIT_NEXT_DAY_MAX_DAYS}，机制终止")
    else:
        adj.update({
            "enabled": True,
            "stop_loss_price": stop_loss_price,
            "sell_ratio": sell_ratio,
            "days_count": days_count
        })
        print(f"【次日调整机制】初始化完成 "
              f"止损价:{stop_loss_price:.4f} 卖出比例:{sell_ratio * 100:.1f}% 天数:{days_count}/{DYNAMIC_PROFIT_NEXT_DAY_MAX_DAYS}")

def check_dynamic_profit_next_day_adjustment(day_data: DayData, current_price: float,
                                             available_position: int) -> Optional[int]:
    """
    返回：若触发卖出，返回卖出数量；否则 None
    """
    if not DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED:
        return None
    adj = day_data.dynamic_profit_next_day_adjustment
    if not adj.get("enabled", False):
        return None
    stop_loss_price = adj.get("stop_loss_price", -float("inf"))
    if stop_loss_price <= 0:
        return None
    trigger_price = stop_loss_price - DYNAMIC_PROFIT_NEXT_DAY_STOP_LOSS_PRICE_OFFSET
    if current_price > trigger_price:
        return None
    sell_ratio = adj.get("sell_ratio", 0.0)
    if sell_ratio <= 0:
        return None
    sell_qty = int(available_position * sell_ratio)
    sell_qty = (sell_qty // 100) * 100
    if sell_qty <= 0:
        print(f"【次日调整机制】{day_data} 无可用持仓，跳过卖出")
        return None
    print(f"【次日调整机制触发】价格跌破固定止损线，卖出{sell_qty}股")
    adj["enabled"] = False
    return sell_qty

def update_dynamic_profit_high_lines(day_data: DayData, condition_type: str,
                                     current_profit_line: float) -> None:
    if not DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED:
        return
    adj = day_data.dynamic_profit_next_day_adjustment
    if condition_type == "condition2":
        old = adj.get("condition2_high_line", -float("inf"))
        if current_profit_line > old:
            adj["condition2_high_line"] = current_profit_line
            adj["condition2_activated"] = True
    elif condition_type == "condition9":
        old = adj.get("condition9_high_line", -float("inf"))
        if current_profit_line > old:
            adj["condition9_high_line"] = current_profit_line
            adj["condition9_activated"] = True

def disable_next_day_adjustment_if_dynamic_profit_triggered(day_data: DayData, condition_type: str) -> None:
    if not DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED:
        return
    adj = day_data.dynamic_profit_next_day_adjustment
    if adj.get("enabled", False):
        adj["enabled"] = False
        print(f"【次日调整机制】动态止盈{condition_type}再次触发，固定止损机制失效")