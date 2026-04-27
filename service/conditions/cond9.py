# service/conditions/cond9.py
# -*- coding: utf-8 -*-
"""
条件9：第一区间动态止盈
"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any
from domain.contexts.condition9 import Condition9Context
from config.strategy.config_objects import Condition9Config, load_strategy_config
from .utils import _check_dynamic_profit_core

logger = logging.getLogger(__name__)


def check_condition9(
    context: Condition9Context,
    increase: float,
    current_price: float,
    base_price: float,
    board_break_active: bool = False,
    condition2_active: bool = False,
    config: Optional[Condition9Config] = None,
) -> Optional[Dict[str, Any]]:
    if config is None:
        config = load_strategy_config().condition9

    # 区间停止检查
    if context.condition9_stopped:
        return None
    upper_band = context.condition9_upper_band
    lower_band = context.condition9_lower_band
    if current_price > upper_band:
        context.condition9_stopped = True
        context.condition9_triggered = False
        logger.info('【条件9停止监测】价格突破区间上限，停止监测')
        return None
    if not (lower_band <= current_price <= upper_band):
        return None

    def _priority_check():
        if condition2_active:
            if context.condition9_triggered:
                context.condition9_triggered = False
                context.condition9_high_price = -float('inf')
                context.condition9_profit_line = -float('inf')
                logger.info("【优先级覆盖】条件二激活，条件九状态被清理")
            return True
        return False

    return _check_dynamic_profit_core(
        context=context,
        increase=increase,
        current_price=current_price,
        base_price=base_price,
        config=config,
        condition_name='条件9',
        board_break_active=board_break_active,
        priority_check_fn=_priority_check,
        get_triggered=lambda c: c.condition9_triggered,
        set_triggered=lambda c, v: setattr(c, 'condition9_triggered', v),
        get_high_price=lambda c: c.condition9_high_price,
        set_high_price=lambda c, v: setattr(c, 'condition9_high_price', v),
        get_profit_line=lambda c: c.condition9_profit_line,
        set_profit_line=lambda c, v: setattr(c, 'condition9_profit_line', v),
        get_sell_times=lambda c: c.condition9_sell_times,
        inc_sell_times=lambda c: setattr(c, 'condition9_sell_times', c.condition9_sell_times + 1),
    )