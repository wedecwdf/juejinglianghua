# domain/conditions/pyramid_add.py
# -*- coding: utf-8 -*-
"""动态回调加仓条件包装"""
from __future__ import annotations
from typing import Optional
from domain.decisions import Condition, Decision, DecisionType
from service.pyramid_service import check_callback_strategy


class PyramidAddCondition(Condition):
    def evaluate(self, symbol: str, current_price: float, available_position: int,
                 day_data, base_price: float, ctx) -> Optional[Decision]:
        result = check_callback_strategy(symbol, current_price, store=ctx.callback_store)
        if result:
            return Decision(
                condition_name='callback_addition',
                decision_type=DecisionType.BUY,
                symbol=symbol,
                price=current_price,
                quantity=result['quantity'],
                reason=result['reason'],
                extra={'trigger_data': result.get('trigger_data', {})}
            )
        return None