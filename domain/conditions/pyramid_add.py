# domain/conditions/pyramid_add.py
from __future__ import annotations
from typing import Callable
from domain.decisions import Condition, Decision, DecisionType


class PyramidAddCondition(Condition):
    condition_name = 'pyramid_add'
    is_side_effect = False
    depends_on = []

    def __init__(self, check_fn: Callable, complete_fn: Callable) -> None:
        """
        :param check_fn: 检查函数，check_callback_strategy(symbol, current_price, store) -> Optional[dict]
        :param complete_fn: 完成回调函数，complete_callback_task(symbol, store) -> None
        """
        self._check_fn = check_fn
        self._complete_fn = complete_fn

    def evaluate(self, symbol, current_price, available_position, day_data,
                 base_price, ctx, shared_state):
        result = self._check_fn(symbol, current_price, store=ctx.callback_store)
        if result:
            return PyramidAddDecision(
                symbol=symbol,
                price=current_price,
                quantity=result['quantity'],
                reason=result['reason'],
                complete_fn=self._complete_fn,
            )
        return None


class PyramidAddDecision(Decision):
    def __init__(self, symbol, price, quantity, reason, complete_fn: Callable):
        super().__init__(
            condition_name='callback_addition',
            decision_type=DecisionType.BUY,
            symbol=symbol,
            price=price,
            quantity=quantity,
            reason=reason,
        )
        self._complete_fn = complete_fn

    def apply(self, ctx):
        self._complete_fn(self.symbol, store=ctx.callback_store)