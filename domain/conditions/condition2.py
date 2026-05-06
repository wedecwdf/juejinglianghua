# domain/conditions/condition2.py
# -*- coding: utf-8 -*-
"""
条件2动态止盈条件包装器，通过构造函数注入检查函数和数量计算函数，
不再直接依赖 service 层。
"""

from __future__ import annotations
from typing import Optional, Callable
from domain.decisions import Condition, Decision, DecisionType


class Condition2Condition(Condition):
    condition_name = 'condition2'
    is_side_effect = False
    depends_on = []

    def __init__(self, check_fn: Callable, sell_qty_fn: Callable) -> None:
        """
        :param check_fn: 签名 (context2, increase, current_price, base_price,
                         board_break_active, config) -> Optional[dict]
        :param sell_qty_fn: 签名 (available_position, percent) -> int
        """
        self._check_fn = check_fn
        self._sell_qty_fn = sell_qty_fn

    def evaluate(self, symbol, current_price, available_position, day_data,
                 base_price, ctx, shared_state):
        context2 = ctx.context_store.get('condition2', symbol,
                                         factory=lambda: self._create_context())
        increase = (current_price - base_price) / base_price if base_price > 0 else 0
        res = self._check_fn(context2, increase, current_price, base_price,
                             board_break_active=False,
                             config=ctx.config.condition2)
        if res:
            qty = self._sell_qty_fn(available_position, res["sell_percent"])
            if qty:
                return Condition2Decision(
                    symbol=symbol,
                    price=current_price - res["sell_price_offset"],
                    quantity=qty,
                    reason=res["reason"],
                    extra={'trigger_data': res['trigger_data']}
                )
        return None

    @staticmethod
    def _create_context():
        from domain.contexts.condition2 import Condition2Context
        return Condition2Context()


class Condition2Decision(Decision):
    def __init__(self, symbol, price, quantity, reason, extra=None):
        super().__init__(
            condition_name='condition2',
            decision_type=DecisionType.SELL,
            symbol=symbol,
            price=price,
            quantity=quantity,
            reason=reason,
            extra=extra or {}
        )

    def apply(self, ctx):
        context2 = ctx.context_store.get('condition2', self.symbol)
        context2.dynamic_profit_sell_times += 1
        ctx.session_registry.increment_total_sell_times(self.symbol, 1)
        context2.condition2_triggered_and_sold = True
        try:
            context9 = ctx.context_store.get('condition9', self.symbol)
            context9.condition9_triggered = False
            context9.condition9_high_price = -float('inf')
            context9.condition9_profit_line = -float('inf')
        except KeyError:
            pass