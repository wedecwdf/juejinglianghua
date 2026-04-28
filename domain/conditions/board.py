# domain/conditions/board.py
from domain.decisions import Condition, Decision, DecisionType
from domain.conditions.registry import ConditionRegistry
from service.board_service import (
    handle_board_counting,
    handle_dynamic_profit_on_board_break
)


@ConditionRegistry.register(priority=8)  # 优先级最低，仅副作用
class BoardCountingCondition(Condition):
    """
    板数计数与状态更新（副作用），不返回 Decision。
    必须执行，但不参与仲裁。在 trade_engine 中单独调用。
    """
    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx):
        board_status = ctx.board_repo.get_board_status(symbol)
        board_count_data = ctx.board_repo.get_board_count_data(symbol)
        prev_close = board_status.prev_close if board_status else 0.0
        # 更新封板计数和状态机
        new_count = handle_board_counting(symbol, current_price, prev_close,
                                          ctx.tick_time, board_status, board_count_data)
        if new_count is not None:
            ctx.board_repo.set_board_count_data(symbol, new_count)
        return None   # 永远不生成决策


@ConditionRegistry.register(priority=2)  # 炸板卖出优先级与条件2相同，这里暂时按2处理，实际可调整
class BoardBreakSellCondition(Condition):
    """炸板动态止盈卖出决策"""
    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx):
        board_status = ctx.board_repo.get_board_status(symbol)
        qty = handle_dynamic_profit_on_board_break(symbol, current_price, available_position,
                                                   day_data, board_status, ctx.session_registry)
        if qty:
            return BoardBreakSellDecision(symbol=symbol,
                                          price=current_price - 0.01,   # 从配置读取
                                          quantity=qty,
                                          reason='炸板动态止盈卖出')
        return None


class BoardBreakSellDecision(Decision):
    def __init__(self, symbol, price, quantity, reason):
        super().__init__(
            condition_name='board_dynamic_profit',
            decision_type=DecisionType.SELL,
            symbol=symbol,
            price=price,
            quantity=quantity,
            reason=reason,
        )

    def apply(self, ctx):
        # 板数状态已在内部更新，此处无需额外操作
        pass