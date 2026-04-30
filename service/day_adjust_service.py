# service/day_adjust_service.py
# -*- coding: utf-8 -*-
"""
次日固定止损机制，使用配置对象替代全局常量。
模块级 config 通过 set_config 注入。
"""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional
from domain.contexts.next_day import NextDayAdjustmentContext
from config.strategy.config_objects import Condition2Config

logger = logging.getLogger(__name__)

# 模块级默认配置，由外部注入
_config: Optional[Condition2Config] = None


def set_config(config: Condition2Config):
    global _config
    _config = config


def initialize_next_day_adjustment(adj_ctx: NextDayAdjustmentContext, prev_close_price: float) -> None:
    if not _config or not _config.next_day_adjustment_enabled:
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
        sell_ratio += (_config.sell_percent_high if inc >= _config.dynamic_line_threshold else _config.sell_percent_low)
    if c9_activated:
        inc = (c9_high - prev_close_price) / prev_close_price
        sell_ratio += (_config.sell_percent_high if inc >= _config.dynamic_line_threshold else _config.sell_percent_low)  # 注意：条件9使用条件2的阈值？原逻辑如此

    sell_ratio = min(sell_ratio, _config.next_day_max_sell_ratio)
    days_count = data.get("days_count", 0) + 1
    if days_count > _config.next_day_max_days:
        data["enabled"] = False
        logger.info("【次日调整机制】达到最大延续天数%d，机制终止", _config.next_day_max_days)
    else:
        data.update({
            "enabled": True,
            "stop_loss_price": stop_loss_price,
            "sell_ratio": sell_ratio,
            "days_count": days_count
        })
        logger.info("【次日调整机制】初始化完成 止损价:%.4f 卖出比例:%.1f%% 天数:%d/%d",
                    stop_loss_price, sell_ratio * 100, days_count, _config.next_day_max_days)


def check_dynamic_profit_next_day_adjustment(adj_ctx: NextDayAdjustmentContext,
                                            current_price: float,
                                            available_position: int) -> Optional[int]:
    if not _config or not _config.next_day_adjustment_enabled:
        return None
    data = adj_ctx.data
    if not data.get("enabled", False):
        return None
    stop_loss_price = data.get("stop_loss_price", -float("inf"))
    trigger_price = stop_loss_price - _config.next_day_stop_loss_offset
    if current_price > trigger_price:
        return None
    sell_ratio = data.get("sell_ratio", 0.0)
    sell_qty = int(available_position * sell_ratio)
    sell_qty = (sell_qty // 100) * 100
    if sell_qty <= 0:
        return None
    data["enabled"] = False
    logger.info("【次日调整机制触发】价格跌破固定止损线，卖出%d股", sell_qty)
    return sell_qty


def update_dynamic_profit_high_lines(adj_ctx: NextDayAdjustmentContext, condition_type: str,
                                    current_profit_line: float) -> None:
    if not _config or not _config.next_day_adjustment_enabled:
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
    if not _config or not _config.next_day_adjustment_enabled:
        return
    data = adj_ctx.data
    if data.get("enabled", False):
        data["enabled"] = False
        logger.info("【次日调整机制】动态止盈%s再次触发，固定止损机制失效", condition_type)