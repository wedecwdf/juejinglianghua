# domain/conditions/condition2.py
from domain.decisions import Condition, Decision, DecisionType
from service.condition_service import check_condition2
from service.order_executor import sell_qty_by_percent


class Condition2Condition(Condition):
    condition_name = 'condition2'
    is_side_effect = False
    depends_on = []

    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx, shared_state):
        context2 = ctx.context_store.get('condition2', symbol,
                                         factory=lambda: self._create_context())
        increase = (current_price - base_price) / base_price if base_price > 0 else 0
        res = check_condition2(context2, increase, current_price, base_price,
                               board_break_active=False,
                               config=ctx.config.condition2)
        if res:
            qty = sell_qty_by_percent(available_position, res["sell_percent"])
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
        # 清理条件9（保留原逻辑）
        try:
            context9 = ctx.context_store.get('condition9', self.symbol)
            context9.condition9_triggered = False
            context9.condition9_high_price = -float('inf')
            context9.condition9_profit_line = -float('inf')
        except KeyError:
            pass