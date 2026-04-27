# domain/conditions/condition8_grid.py
# -*- coding: utf-8 -*-
"""条件8动态基准价网格交易包装"""
from __future__ import annotations
from typing import Optional
from domain.decisions import Condition, Decision, DecisionType
from service.condition_service import check_condition8
from config.strategy import CONDITION8_MAX_TOTAL_QUANTITY, CONDITION8_MULTIPLE_ORDER_ENABLED


class Condition8GridCondition(Condition):
    def evaluate(self, symbol: str, current_price: float, available_position: int,
                 day_data, base_price: float, ctx) -> Optional[Decision]:
        context8 = ctx.session_registry.get_condition8(symbol, base_price)
        res = check_condition8(day_data, context8, current_price, available_position,
                               order_ledger=ctx.order_ledger)
        if not res:
            return None

        total_sell_today = context8.condition8_total_sell_today
        total_buy_today = context8.condition8_total_buy_today
        max_total = CONDITION8_MAX_TOTAL_QUANTITY.get(symbol, 0)
        qty = res["quantity"]
        side = res["side"]

        if side == "sell" and total_sell_today + qty <= max_total:
            return Decision(
                condition_name='condition8',
                decision_type=DecisionType.SELL,
                symbol=symbol,
                price=current_price,
                quantity=qty,
                reason=res["reason"],
                extra={'trigger_data': res['trigger_data']}
            )
        elif side == "buy" and total_buy_today + qty <= max_total:
            return Decision(
                condition_name='condition8',
                decision_type=DecisionType.BUY,
                symbol=symbol,
                price=current_price,
                quantity=qty,
                reason=res["reason"],
                extra={'trigger_data': res['trigger_data']}
            )
        return None