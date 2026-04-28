# domain/conditions/pyramid_profit.py
from domain.decisions import Condition, Decision, DecisionType
from domain.conditions.registry import ConditionRegistry
from service.conditions import check_pyramid_profit
from config.strategy.config_objects import PyramidProfitConfig


@ConditionRegistry.register(priority=7)
class PyramidProfitCondition(Condition):
    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx):
        context = ctx.context_store.get('pyramid', symbol,
                                        factory=lambda: self._create_context(base_price))
        res = check_pyramid_profit(symbol, context, current_price, available_position)
        if res:
            return PyramidProfitDecision(
                symbol=symbol,
                price=current_price - ctx.config.pyramid.sell_price_offset,
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