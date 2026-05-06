# domain/conditions/board.py
# -*- coding: utf-8 -*-
"""
板数相关条件包装器，完全解耦 service 实现。
所有业务函数通过构造函数注入。
"""

from domain.decisions import Condition, Decision, DecisionType
from typing import Callable


class BoardCountingCondition(Condition):
    condition_name = 'board_counting'
    is_side_effect = True
    depends_on = []

    def __init__(self, counting_fn: Callable) -> None:
        """
        :param counting_fn: handle_board_counting(symbol, current_price, prev_close,
                             tick_time, board_status, board_count_data) -> new_count
        """
        self._counting_fn = counting_fn

    def evaluate(self, symbol, current_price, available_position, day_data,
                 base_price, ctx, shared_state):
        board_status = ctx.board_repo.get_board_status(symbol)
        board_count_data = ctx.board_repo.get_board_count_data(symbol)
        prev_close = board_status.prev_close if board_status else 0.0
        new_count = self._counting_fn(symbol, current_price, prev_close,
                                      ctx.tick_time, board_status, board_count_data)
        if new_count is not None:
            ctx.board_repo.set_board_count_data(symbol, new_count)
        return None


class BoardBreakSellCondition(Condition):
    condition_name = 'board_break_sell'
    is_side_effect = False
    depends_on = []

    def __init__(self, dynamic_profit_fn: Callable) -> None:
        """
        :param dynamic_profit_fn: handle_dynamic_profit_on_board_break(
            symbol, current_price, available_position, day_data,
            board_status, context_store) -> Optional[int]
        """
        self._dynamic_profit_fn = dynamic_profit_fn

    def evaluate(self, symbol, current_price, available_position, day_data,
                 base_price, ctx, shared_state):
        board_status = ctx.board_repo.get_board_status(symbol)
        qty = self._dynamic_profit_fn(symbol, current_price, available_position,
                                      day_data, board_status,
                                      ctx.context_store)
        if qty:
            return BoardBreakSellDecision(
                symbol=symbol,
                price=current_price - 0.01,
                quantity=qty,
                reason='炸板动态止盈卖出'
            )
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
        pass