# service/day_adjust_service.py
# -*- coding: utf-8 -*-
"""
次日固定止损机制，使用 NextDayAdjustmentContext
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from domain.contexts.next_day import NextDayAdjustmentContext
from config.strategy import (
    DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED,
    DYNAMIC_PROFIT_NEXT_DAY_STOP_LOSS_PRICE_OFFSET,
    DYNAMIC_PROFIT_NEXT_DAY_MAX_SELL_RATIO,
    DYNAMIC_PROFIT_NEXT_DAY_MAX_DAYS,
    CONDITION2_DYNAMIC_LINE_THRESHOLD, CONDITION2_SELL_PERCENT_HIGH, CONDITION2_SELL_PERCENT_LOW,
    CONDITION9_DYNAMIC_LINE_THRESHOLD, CONDITION9_SELL_PERCENT_HIGH, CONDITION9_SELL_PERCENT_LOW
)

def initialize_next_day_adjustment(adj_ctx: NextDayAdjustmentContext, prev_close_price: float) -> None:
    if not DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED:
        return
    data = adj_ctx.data
    c2_activated = data.get("condition2_activated", False)
    c9_activated = data.get("condition9_activated", False)
    if not (c2_activated or c9_activated):
        data["enabled"] = False
        return

    c2_high = data.get("condition2_high_line", -float("inf"))
    c9_high = data.get("condition9_high_line", -float("inf"))
    stop_loss_price = max(c2_high, c9_high)
    if stop_loss_price <= 0:
        data["enabled"] = False
        return

    sell_ratio = 0.0
    if c2_activated:
        inc = (c2_high - prev_close_price) / prev_close_price
        sell_ratio += (CONDITION2_SELL_PERCENT_HIGH if inc >= CONDITION2_DYNAMIC_LINE_THRESHOLD else CONDITION2_SELL_PERCENT_LOW)
    if c9_activated:
        inc = (c9_high - prev_close_price) / prev_close_price
        sell_ratio += (CONDITION9_SELL_PERCENT_HIGH if inc >= CONDITION9_DYNAMIC_LINE_THRESHOLD else CONDITION9_SELL_PERCENT_LOW)

    sell_ratio = min(sell_ratio, DYNAMIC_PROFIT_NEXT_DAY_MAX_SELL_RATIO)
    days_count = data.get("days_count", 0) + 1
    if days_count > DYNAMIC_PROFIT_NEXT_DAY_MAX_DAYS:
        data["enabled"] = False
    else:
        data.update({
            "enabled": True,
            "stop_loss_price": stop_loss_price,
            "sell_ratio": sell_ratio,
            "days_count": days_count
        })

def check_dynamic_profit_next_day_adjustment(adj_ctx: NextDayAdjustmentContext,
                                            current_price: float,
                                            available_position: int) -> Optional[int]:
    if not DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED:
        return None
    data = adj_ctx.data
    if not data.get("enabled", False):
        return None
    stop_loss_price = data.get("stop_loss_price", -float("inf"))
    trigger_price = stop_loss_price - DYNAMIC_PROFIT_NEXT_DAY_STOP_LOSS_PRICE_OFFSET
    if current_price > trigger_price:
        return None
    sell_ratio = data.get("sell_ratio", 0.0)
    sell_qty = int(available_position * sell_ratio)
    sell_qty = (sell_qty // 100) * 100
    if sell_qty <= 0:
        return None
    data["enabled"] = False
    return sell_qty

def update_dynamic_profit_high_lines(adj_ctx: NextDayAdjustmentContext, condition_type: str,
                                    current_profit_line: float) -> None:
    if not DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED:
        return
    data = adj_ctx.data
    if condition_type == "condition2":
        old = data.get("condition2_high_line", -float("inf"))
        if current_profit_line > old:
            data["condition2_high_line"] = current_profit_line
            data["condition2_activated"] = True
    elif condition_type == "condition9":
        old = data.get("condition9_high_line", -float("inf"))
        if current_profit_line > old:
            data["condition9_high_line"] = current_profit_line
            data["condition9_activated"] = True

def disable_next_day_adjustment_if_dynamic_profit_triggered(adj_ctx: NextDayAdjustmentContext, condition_type: str) -> None:
    if not DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED:
        return
    data = adj_ctx.data
    if data.get("enabled", False):
        data["enabled"] = False