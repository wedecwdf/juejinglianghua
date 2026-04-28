# domain/conditions/pyramid_add.py
from domain.decisions import Condition, Decision, DecisionType
from service.pyramid_service import check_callback_strategy


class PyramidAddCondition(Condition):
    condition_name = 'pyramid_add'
    is_side_effect = False
    depends_on = []

    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx, shared_state):
        result = check_callback_strategy(symbol, current_price, store=ctx.callback_store)
        if result:
            return PyramidAddDecision(
                symbol=symbol,
                price=current_price,
                quantity=result['quantity'],
                reason=result['reason'],
            )
        return None


class PyramidAddDecision(Decision):
    def __init__(self, symbol, price, quantity, reason):
        super().__init__(
            condition_name='callback_addition',
            decision_type=DecisionType.BUY,
            symbol=symbol,
            price=price,
            quantity=quantity,
            reason=reason,
        )

    def apply(self, ctx):
        from service.pyramid_service import complete_callback_task
        complete_callback_task(self.symbol, store=ctx.callback_store)