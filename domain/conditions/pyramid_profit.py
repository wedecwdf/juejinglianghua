# domain/conditions/pyramid_profit.py
# -*- coding: utf-8 -*-
"""金字塔止盈条件包装"""
from __future__ import annotations
from typing import Optional
from domain.decisions import Condition, Decision, DecisionType
from service.conditions import check_pyramid_profit
from config.strategy import PYRAMID_PROFIT_SELL_PRICE_OFFSET


class PyramidProfitCondition(Condition):
    def evaluate(self, symbol: str, current_price: float, available_position: int,
                 day_data, base_price: float, ctx) -> Optional[Decision]:
        if available_position <= 0:
            return None
        context = ctx.session_registry.get_pyramid(symbol, base_price)
        res = check_pyramid_profit(symbol, context, current_price, available_position)
        if res:
            return Decision(
                condition_name='pyramid_profit',
                decision_type=DecisionType.SELL,
                symbol=symbol,
                price=current_price - PYRAMID_PROFIT_SELL_PRICE_OFFSET,
                quantity=res["quantity"],
                reason=res["reason"],
                extra={'trigger_data': res['trigger_data']}
            )
        return None