# domain/conditions/ma.py
# -*- coding: utf-8 -*-
"""
MA均线交易条件包装器，通过配置对象传递参数。
"""
from domain.decisions import Condition, Decision, DecisionType
from service.condition_service import check_condition4, check_condition5, check_condition6, check_condition7


class MaTradingCondition(Condition):
    condition_name = 'ma_trading'
    is_side_effect = False
    depends_on = []

    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx, shared_state):
        context47 = ctx.context_store.get('condition4_7', symbol,
                                          factory=lambda: self._create_context())
        total_buy = ctx.session_registry.get_total_buy_quantity(symbol)
        ma_config = ctx.config.ma

        if ma_config.condition4_enabled:
            res = check_condition4(day_data, context47, current_price, ma_config)
            if res and total_buy + res["quantity"] <= 10000:
                return MaBuyDecision(symbol, current_price, res["quantity"],
                                     res["reason"], 'condition4',
                                     {'trigger_data': res['trigger_data']})
        if ma_config.condition5_enabled:
            res = check_condition5(day_data, context47, current_price, ma_config)
            if res and total_buy + res["quantity"] <= 10000:
                return MaBuyDecision(symbol, current_price, res["quantity"],
                                     res["reason"], 'condition5',
                                     {'trigger_data': res['trigger_data']})
        if ma_config.condition6_enabled:
            res = check_condition6(day_data, context47, current_price, ma_config)
            if res and total_buy + res["quantity"] <= 10000:
                return MaBuyDecision(symbol, current_price, res["quantity"],
                                     res["reason"], 'condition6',
                                     {'trigger_data': res['trigger_data']})

        if ma_config.condition7_enabled:
            res = check_condition7(day_data, context47, current_price, ctx.tick_time, ma_config)
            if res and total_buy > 0:
                return MaSellDecision(symbol, current_price - res["sell_price_offset"],
                                      total_buy, res["reason"],
                                      {'trigger_data': res['trigger_data']})

        return None

    @staticmethod
    def _create_context():
        from domain.contexts.condition4_7 import Condition4To7Context
        return Condition4To7Context()


class MaBuyDecision(Decision):
    def __init__(self, symbol, price, quantity, reason, name, extra):
        super().__init__(
            condition_name=name,
            decision_type=DecisionType.BUY,
            symbol=symbol,
            price=price,
            quantity=quantity,
            reason=reason,
            extra=extra,
        )

    def apply(self, ctx):
        ctx.session_registry.set_total_buy_quantity(
            self.symbol,
            ctx.session_registry.get_total_buy_quantity(self.symbol) + self.quantity
        )
        context47 = ctx.context_store.get('condition4_7', self.symbol)
        setattr(context47, f'buy_{self.condition_name}_triggered', True)


class MaSellDecision(Decision):
    def __init__(self, symbol, price, quantity, reason, extra):
        super().__init__(
            condition_name='condition7',
            decision_type=DecisionType.SELL,
            symbol=symbol,
            price=price,
            quantity=quantity,
            reason=reason,
            extra=extra,
        )

    def apply(self, ctx):
        context47 = ctx.context_store.get('condition4_7', self.symbol)
        context47.condition7_triggered = True
        ctx.session_registry.reset_total_buy(self.symbol)