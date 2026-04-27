# domain/conditions/ma.py
# -*- coding: utf-8 -*-
"""MA均线交易条件包装"""
from __future__ import annotations
from typing import Optional
from domain.decisions import Condition, Decision, DecisionType
from service.condition_service import check_condition4, check_condition5, check_condition6, check_condition7
from config.strategy import CONDITION8_MAX_TOTAL_QUANTITY


class MaTradingCondition(Condition):
    def evaluate(self, symbol: str, current_price: float, available_position: int,
                 day_data, base_price: float, ctx) -> Optional[Decision]:
        context47 = ctx.session_registry.get_condition4_7(symbol)
        total_buy = ctx.session_registry.get_total_buy_quantity(symbol)
        max_total = CONDITION8_MAX_TOTAL_QUANTITY.get(symbol, 0)

        for cond_fn, name in [(check_condition4, "condition4"),
                              (check_condition5, "condition5"),
                              (check_condition6, "condition6")]:
            res = cond_fn(day_data, context47, current_price)
            if res:
                if total_buy + res["quantity"] > max_total:
                    return None  # 超出上限，跳过（但不卖）
                return Decision(
                    condition_name=name,
                    decision_type=DecisionType.BUY,
                    symbol=symbol,
                    price=current_price,
                    quantity=res["quantity"],
                    reason=res["reason"],
                    extra={'trigger_data': res['trigger_data']}
                )

        res = check_condition7(day_data, context47, current_price, ctx.tick_time)
        if res and total_buy > 0:
            return Decision(
                condition_name='condition7',
                decision_type=DecisionType.SELL,
                symbol=symbol,
                price=current_price - res["sell_price_offset"],
                quantity=total_buy,
                reason=res["reason"],
                extra={'trigger_data': res['trigger_data']}
            )
        return None