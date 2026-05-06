# domain/conditions/pyramid_profit.py
# -*- coding: utf-8 -*-
"""
金字塔止盈条件包装器，注入检查函数、PyramidProfitConfig 和 Condition8Config。
"""

from domain.decisions import Condition, Decision, DecisionType
from typing import Callable
from config.strategy.config_objects import PyramidProfitConfig, Condition8Config


class PyramidProfitCondition(Condition):
    condition_name = 'pyramid_profit'
    is_side_effect = False
    depends_on = []

    def __init__(self, check_fn: Callable,
                 pyramid_config: PyramidProfitConfig,
                 condition8_config: Condition8Config) -> None:
        self._check_fn = check_fn
        self._pyramid_config = pyramid_config
        self._condition8_config = condition8_config

    def evaluate(self, symbol, current_price, available_position, day_data,
                 base_price, ctx, shared_state):
        context = ctx.context_store.get('pyramid', symbol,
                                        factory=lambda: self._create_context(base_price))
        res = self._check_fn(
            symbol, context, current_price, available_position,
            self._pyramid_config,
            self._condition8_config
        )
        if res:
            return PyramidProfitDecision(
                symbol=symbol,
                price=current_price - self._pyramid_config.sell_price_offset,
                quantity=res["quantity"],
                reason=res["reason"],
                extra={'trigger_data': res['trigger_data']}
            )
        return None

    @staticmethod
    def _create_context(base_price):
        from domain.contexts.pyramid import PyramidContext
        return PyramidContext(base_price)


class PyramidProfitDecision(Decision):
    def __init__(self, symbol, price, quantity, reason, extra):
        super().__init__(
            condition_name='pyramid_profit',
            decision_type=DecisionType.SELL,
            symbol=symbol,
            price=price,
            quantity=quantity,
            reason=reason,
            extra=extra,
        )

    def apply(self, ctx):
        context = ctx.context_store.get('pyramid', self.symbol)
        trigger_data = self.extra.get('trigger_data', {})
        level = trigger_data.get('pyramid_level', 0)
        context.pyramid_profit_status[level] = True
        context.pyramid_profit_triggered = True