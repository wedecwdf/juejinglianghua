# service/conditions/cond2.py
# -*- coding: utf-8 -*-
"""
条件2：动态止盈，接收配置对象实现依赖注入。
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from domain.contexts.condition2 import Condition2Context
from config.strategy.config_objects import Condition2Config, load_strategy_config
from .utils import _check_dynamic_profit_core

def check_condition2(
    context: Condition2Context,
    increase: float,
    current_price: float,
    base_price: float,
    board_break_active: bool = False,
    config: Optional[Condition2Config] = None,
) -> Optional[Dict[str, Any]]:
    if config is None:
        config = load_strategy_config().condition2  # 默认使用全局配置
    return _check_dynamic_profit_core(
        context=context,
        increase=increase,
        current_price=current_price,
        base_price=base_price,
        config=config,
        condition_name='条件2',
        board_break_active=board_break_active,
        get_triggered=lambda c: c.dynamic_profit_triggered,
        set_triggered=lambda c, v: setattr(c, 'dynamic_profit_triggered', v),
        get_high_price=lambda c: c.dynamic_profit_high_price,
        set_high_price=lambda c, v: setattr(c, 'dynamic_profit_high_price', v),
        get_profit_line=lambda c: c.dynamic_profit_line,
        set_profit_line=lambda c, v: setattr(c, 'dynamic_profit_line', v),
        get_sell_times=lambda c: c.dynamic_profit_sell_times,
        inc_sell_times=lambda c: setattr(c, 'dynamic_profit_sell_times', c.dynamic_profit_sell_times + 1),
    )