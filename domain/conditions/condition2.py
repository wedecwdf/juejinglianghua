# domain/conditions/condition2.py
from domain.decisions import Condition, Decision, DecisionType
from service.condition_service import check_condition2
from service.order_executor import sell_qty_by_percent

class Condition2Condition(Condition):
    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx):
        context2 = ctx.session_registry.get_condition2(symbol)
        increase = (current_price - base_price) / base_price if base_price > 0 else 0
        board_break_active = False  # 需从外部获取，此处暂简化
        res = check_condition2(context2, increase, current_price, base_price,
                               board_break_active=board_break_active,
                               config=ctx.config.condition2)
        if res:
            qty = sell_qty_by_percent(available_position, res["sell_percent"])
            if qty:
                return Decision(
                    condition_name='condition2',
                    decision_type=DecisionType.SELL,
                    symbol=symbol,
                    price=current_price - res["sell_price_offset"],
                    quantity=qty,
                    reason=res["reason"],
                    extra={'trigger_data': res['trigger_data']}
                )
        return None