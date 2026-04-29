# domain/conditions/condition9.py
# -*- coding: utf-8 -*-
"""
条件9第一区间动态止盈条件包装器，通过配置注入上下文。
"""
from __future__ import annotations
from typing import Optional
from domain.decisions import Condition, Decision, DecisionType
from service.condition_service import check_condition9
from service.order_executor import sell_qty_by_percent


class Condition9Condition(Condition):
    condition_name = 'condition9'
    is_side_effect = False
    depends_on = ['condition2']

    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx, shared_state):
        config = ctx.config.condition9
        context9 = ctx.context_store.get('condition9', symbol,
                                         factory=lambda: self._create_context(base_price, config))
        increase = (current_price - base_price) / base_price if base_price > 0 else 0
        condition2_active = shared_state.get('condition2_active', False)
        res = check_condition9(context9, increase, current_price, base_price,
                               board_break_active=False,
                               condition2_active=condition2_active,
                               config=config)
        if res:
            qty = sell_qty_by_percent(available_position, res["sell_percent"])
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
    def _create_context(base_price, config):
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