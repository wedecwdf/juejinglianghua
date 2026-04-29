# domain/conditions/condition8_grid.py
# -*- coding: utf-8 -*-
"""
条件8动态基准价网格交易包装。
使用拆分后的小接口访问 order 相关功能。
"""
from __future__ import annotations
from typing import Optional
from domain.decisions import Condition, Decision, DecisionType
from service.condition_service import check_condition8
from config.strategy.config_objects import Condition8Config


class Condition8GridCondition(Condition):
    condition_name = 'condition8_grid'
    is_side_effect = False
    depends_on = []

    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx, shared_state):
        # 从上下文获取条件8上下文和需要的 order 功能
        context8 = ctx.context_store.get('condition8', symbol,
                                         factory=lambda: self._create_context(base_price))
        # 注意：check_condition8 需要 order_ledger 参数，这里传入 ctx.order_repo 即可，
        # 因为它实际是 OrderLedgerImpl 实例，拥有 is_cancelling 等方法。
        res = check_condition8(day_data, context8, current_price, available_position,
                               order_ledger=ctx.order_repo)   # 原 ctx.order_ledger 改为 ctx.order_repo
        if not res:
            return None

        total_sell = context8.condition8_total_sell_today
        total_buy = context8.condition8_total_buy_today
        max_total = 10000  # 可用配置
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
    def _create_context(base_price):
        from domain.contexts.condition8 import Condition8Context
        return Condition8Context(base_price)


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