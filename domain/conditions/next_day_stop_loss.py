# domain/conditions/next_day_stop_loss.py
from domain.decisions import Condition, Decision, DecisionType
from service.day_adjust_service import check_dynamic_profit_next_day_adjustment

class NextDayStopLossCondition(Condition):
    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx):
        adj_ctx = ctx.session_registry.get_next_day(symbol)
        qty = check_dynamic_profit_next_day_adjustment(adj_ctx, current_price, available_position)
        if qty:
            return Decision(
                condition_name='next_day_stop_loss',
                decision_type=DecisionType.SELL,
                symbol=symbol,
                price=current_price,
                quantity=qty,
                reason='动态止盈次日调整机制止损',
            )
        return None