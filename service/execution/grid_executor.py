# service/execution/grid_executor.py
# -*- coding: utf-8 -*-
"""条件8网格执行器"""
from __future__ import annotations
from domain.day_data import DayData
from domain.stores import OrderLedger, SessionRegistry
from service.condition_service import check_condition8
from service.order_executor import place_sell, place_buy
from config.strategy import (
    CONDITION8_MAX_TOTAL_QUANTITY,
    CONDITION8_MULTIPLE_ORDER_ENABLED
)

def execute_condition8_grid(symbol: str, current_price: float,
                            available_position: int, day_data: DayData,
                            base_price: float,
                            order_ledger: OrderLedger,
                            session_registry: SessionRegistry) -> bool:
    context = session_registry.get_condition8(symbol, base_price)
    res = check_condition8(day_data, context, current_price, available_position, order_ledger=order_ledger)
    if not res:
        return False

    total_sell_today = context.condition8_total_sell_today
    total_buy_today = context.condition8_total_buy_today
    max_total = CONDITION8_MAX_TOTAL_QUANTITY.get(symbol, 0)
    qty = res["quantity"]
    side = res["side"]
    base_qty = res.get("base_quantity", qty)
    actual_multiple = res.get("actual_multiple", 1)
    stock_type = res.get("stock_type", "default")

    if side == "sell":
        if total_sell_today + qty > max_total:
            print(f"[条件8卖出] {symbol} 累计卖出{total_sell_today}+{qty}将超过上限{max_total}，跳过")
            return True
        place_sell(symbol, current_price, qty, res["reason"], "condition8", res["trigger_data"],
                   order_ledger=order_ledger, session_registry=session_registry)
        context.condition8_trade_times += 1
        context.condition8_last_trade_price = current_price
        context.condition8_last_trigger_price = current_price
        context.condition8_total_sell_today = total_sell_today + qty
    else:
        if total_buy_today + qty > max_total:
            print(f"[条件8买入] {symbol} 累计买入{total_buy_today}+{qty}将超过上限{max_total}，跳过")
            return True
        place_buy(symbol, current_price, qty, res["reason"], "condition8", res["trigger_data"],
                  order_ledger=order_ledger, session_registry=session_registry)
        context.condition8_trade_times += 1
        context.condition8_last_trade_price = current_price
        context.condition8_last_trigger_price = current_price
        context.condition8_total_buy_today = total_buy_today + qty

    if CONDITION8_MULTIPLE_ORDER_ENABLED and actual_multiple > 1:
        print(f"【条件8倍数委托】{symbol} 侧:{side} 数量:{qty} 倍数:{actual_multiple}")
    return True