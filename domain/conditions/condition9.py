# domain/conditions/condition9.py
from domain.decisions import Condition, Decision, DecisionType
from service.condition_service import check_condition9
from service.order_executor import sell_qty_by_percent

class Condition9Condition(Condition):
    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx):
        context9 = ctx.session_registry.get_condition9(symbol, base_price)
        increase = (current_price - base_price) / base_price if base_price > 0 else 0
        context2 = ctx.session_registry.get_condition2(symbol)
        res = check_condition9(context9, increase, current_price, base_price,
                               board_break_active=False,
                               condition2_active=context2.dynamic_profit_triggered,
                               config=ctx.config.condition9)
        if res:
            qty = sell_qty_by_percent(available_position, res["sell_percent"])
            if qty:
                return Decision(
                    condition_name='condition9',
                    decision_type=DecisionType.SELL,
                    symbol=symbol,
                    price=current_price - res["sell_price_offset"],
                    quantity=qty,
                    reason=res["reason"],
                    extra={'trigger_data': res['trigger_data']}
                )
        return None