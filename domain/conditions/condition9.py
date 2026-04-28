# domain/conditions/condition9.py
from domain.decisions import Condition, Decision, DecisionType
from domain.conditions.registry import ConditionRegistry
from service.condition_service import check_condition9
from service.order_executor import sell_qty_by_percent


@ConditionRegistry.register(priority=3)
class Condition9Condition(Condition):
    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx):
        context9 = ctx.context_store.get('condition9', symbol,
                                         factory=lambda: self._create_context(base_price))
        increase = (current_price - base_price) / base_price if base_price > 0 else 0
        context2 = ctx.context_store.get('condition2', symbol)
        res = check_condition9(context9, increase, current_price, base_price,
                               board_break_active=False,
                               condition2_active=context2.dynamic_profit_triggered,
                               config=ctx.config.condition9)
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
    def _create_context(base_price):
        from domain.contexts.condition9 import Condition9Context
        return Condition9Context(base_price)


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