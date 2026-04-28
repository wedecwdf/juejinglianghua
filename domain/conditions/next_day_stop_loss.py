# domain/conditions/next_day_stop_loss.py
from domain.decisions import Condition, Decision, DecisionType
from domain.conditions.registry import ConditionRegistry
from service.day_adjust_service import check_dynamic_profit_next_day_adjustment


@ConditionRegistry.register(priority=1)   # 最高优先级
class NextDayStopLossCondition(Condition):
    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx):
        adj_ctx = ctx.context_store.get('next_day', symbol,
                                        factory=lambda: self._create_context())
        qty = check_dynamic_profit_next_day_adjustment(adj_ctx, current_price, available_position)
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
        # 状态已在 service 内部更新，此处可留空
        pass