# domain/conditions/condition8_grid.py
# -*- coding: utf-8 -*-
"""
条件8动态基准价网格交易包装。
使用配置对象创建 Condition8Context，消除领域层对 config.strategy 的直接依赖。
"""
from __future__ import annotations
from typing import Optional
from domain.decisions import Condition, Decision, DecisionType
from service.condition_service import check_condition8


class Condition8GridCondition(Condition):
    condition_name = 'condition8_grid'
    is_side_effect = False
    depends_on = []

    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx, shared_state):
        config = ctx.config.condition8   # 从 TickContext 获取配置
        context8 = ctx.context_store.get('condition8', symbol,
                                         factory=lambda: self._create_context(base_price, config))
        res = check_condition8(day_data, context8, current_price, available_position,
                               order_ledger=ctx.order_repo)
        if not res:
            return None

        total_sell = context8.condition8_total_sell_today
        total_buy = context8.condition8_total_buy_today
        max_total = config.max_total_quantity.get(symbol, 10000)
        qty = res["quantity"]
        side = res["side"]

        if side == "sell" and total_sell + qty <= max_total:
            return Condition8Decision(
                symbol=symbol, price=current_price, quantity=qty,
                reason=res["reason"], side='sell',
                extra={'trigger_data': res['trigger_data']}
            )
        elif side == "buy" and total_buy + qty <= max_total:
            return Condition8Decision(
                symbol=symbol, price=current_price, quantity=qty,
                reason=res["reason"], side='buy',
                extra={'trigger_data': res['trigger_data']}
            )
        return None

    @staticmethod
    def _create_context(base_price, config):
        from domain.contexts.condition8 import Condition8Context
        return Condition8Context(
            base_price,
            upper_band_percent=config.upper_band_percent,
            lower_band_percent=config.lower_band_percent
        )


class Condition8Decision(Decision):
    def __init__(self, symbol, price, quantity, reason, side, extra):
        super().__init__(
            condition_name='condition8',
            decision_type=DecisionType.SELL if side == 'sell' else DecisionType.BUY,
            symbol=symbol,
            price=price,
            quantity=quantity,
            reason=reason,
            extra=extra,
        )
        self._side = side

    def apply(self, ctx):
        context8 = ctx.context_store.get('condition8', self.symbol)
        if self._side == 'sell':
            context8.condition8_total_sell_today += self.quantity
        else:
            context8.condition8_total_buy_today += self.quantity
        context8.condition8_trade_times += 1
        context8.condition8_last_trade_price = self.price
        context8.condition8_last_trigger_price = self.price