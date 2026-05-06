# domain/conditions/next_day_stop_loss.py
# -*- coding: utf-8 -*-
"""
次日固定止损条件包装器，通过注入检查函数解耦。
模块级 set_config 提前在 main.py 中调用。
"""

from domain.decisions import Condition, Decision, DecisionType
from typing import Callable


class NextDayStopLossCondition(Condition):
    condition_name = 'next_day_stop_loss'
    is_side_effect = False
    depends_on = []

    def __init__(self, check_fn: Callable) -> None:
        """
        :param check_fn: check_dynamic_profit_next_day_adjustment(
            adj_ctx, current_price, available_position) -> Optional[int]
        """
        self._check_fn = check_fn

    def evaluate(self, symbol, current_price, available_position, day_data,
                 base_price, ctx, shared_state):
        adj_ctx = ctx.context_store.get('next_day', symbol,
                                        factory=lambda: self._create_context())
        qty = self._check_fn(adj_ctx, current_price, available_position)
        if qty:
            return NextDayStopLossDecision(
                symbol=symbol,
                price=current_price,
                quantity=qty,
                reason='动态止盈次日调整机制止损',
            )
        return None

    @staticmethod
    def _create_context():
        from domain.contexts.next_day import NextDayAdjustmentContext
        return NextDayAdjustmentContext()


class NextDayStopLossDecision(Decision):
    def __init__(self, symbol, price, quantity, reason):
        super().__init__(
            condition_name='next_day_stop_loss',
            decision_type=DecisionType.SELL,
            symbol=symbol,
            price=price,
            quantity=quantity,
            reason=reason,
        )

    def apply(self, ctx):
        pass