# domain/conditions/condition9.py
# -*- coding: utf-8 -*-
"""
条件9第一区间动态止盈条件包装器，通过构造函数注入检查函数、数量计算函数和配置。
"""

from __future__ import annotations
from typing import Optional, Callable
from domain.decisions import Condition, Decision, DecisionType
from config.strategy.config_objects import Condition9Config


class Condition9Condition(Condition):
    condition_name = 'condition9'
    is_side_effect = False
    depends_on = ['condition2']

    def __init__(self, check_fn: Callable, sell_qty_fn: Callable,
                 config: Condition9Config) -> None:
        self._check_fn = check_fn
        self._sell_qty_fn = sell_qty_fn
        self._config = config

    def evaluate(self, symbol, current_price, available_position, day_data,
                 base_price, ctx, shared_state):
        context9 = ctx.context_store.get('condition9', symbol,
                                         factory=lambda: self._create_context(base_price, self._config))
        increase = (current_price - base_price) / base_price if base_price > 0 else 0
        condition2_active = shared_state.get('condition2_active', False)
        res = self._check_fn(context9, increase, current_price, base_price,
                             board_break_active=False,
                             condition2_active=condition2_active,
                             config=self._config)
        if res:
            qty = self._sell_qty_fn(available_position, res["sell_percent"])
            if qty:
                return Condition9Decision(
                    symbol=symbol,
                    price=current_price - res["sell_price_offset"],
                    quantity=qty,
                    reason=res["reason"],
                    extra={'trigger_data': res['trigger_data']}
                )
        return None

    @staticmethod
    def _create_context(base_price, config: Condition9Config):
        from domain.contexts.condition9 import Condition9Context
        return Condition9Context(
            base_price,
            upper_band_percent=config.upper_band_percent,
            lower_band_percent=config.lower_band_percent
        )


class Condition9Decision(Decision):
    def __init__(self, symbol, price, quantity, reason, extra=None):
        super().__init__(
            condition_name='condition9',
            decision_type=DecisionType.SELL,
            symbol=symbol,
            price=price,
            quantity=quantity,
            reason=reason,
            extra=extra or {}
        )

    def apply(self, ctx):
        context9 = ctx.context_store.get('condition9', self.symbol)
        context9.condition9_sell_times += 1
        ctx.session_registry.increment_total_sell_times(self.symbol, 1)