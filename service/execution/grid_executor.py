# service/execution/grid_executor.py
# -*- coding: utf-8 -*-
"""
条件8动态基准价网格交易执行器（Layer 7）
"""
from __future__ import annotations
from typing import Optional, Dict, Any
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
    res = check_condition8(day_data, current_price, available_position, order_ledger=order_ledger)
    if not res:
        return False

    total_sell_today = getattr(day_data, 'condition8_total_sell_today', 0)
    total_buy_today = getattr(day_data, 'condition8_total_buy_today', 0)
    max_total = CONDITION8_MAX_TOTAL_QUANTITY.get(symbol, 0)

    qty = res["quantity"]
    side = res["side"]
    base_qty = res.get("base_quantity", qty)
    actual_multiple = res.get("actual_multiple", 1)
    skipped_grids = res.get("skipped_grids", 0)
    hit_limit = res.get("hit_limit", False)
    stock_type = res.get("stock_type", "default")
    rise_thr = res.get("rise_threshold", 0)
    decline_thr = res.get("decline_threshold", 0)

    if side == "sell":
        if total_sell_today + qty > max_total:
            print(f"[条件8卖出-独立阈值] {symbol} 累计卖出{total_sell_today}+{qty}将超过上限{max_total}，跳过")
            return True

        type_desc = "高频" if stock_type == "high" else ("低频" if stock_type == "low" else "默认")
        print(f"【条件8独立阈值执行】{symbol} 类型:{type_desc} 上涨阈值:{rise_thr*100:.2f}% 下跌阈值:{decline_thr*100:.2f}%")

        place_sell(symbol, current_price, qty, res["reason"], "condition8", res["trigger_data"],
                   order_ledger=order_ledger, session_registry=session_registry)
        day_data.condition8_trade_times += 1
        day_data.condition8_last_trade_price = current_price
        day_data.condition8_last_trigger_price = current_price
        day_data.condition8_total_sell_today = total_sell_today + qty

        if CONDITION8_MULTIPLE_ORDER_ENABLED and actual_multiple > 1:
            print(f"【条件8倍数委托执行】{symbol} 卖出 {qty}股 (基础{base_qty}×倍数{actual_multiple}) "
                  f"跳过{skipped_grids}个网格{' [已达上限]' if hit_limit else ''}")
        return True
    else:
        if total_buy_today + qty > max_total:
            print(f"[条件8买入-独立阈值] {symbol} 累计买入{total_buy_today}+{qty}将超过上限{max_total}，跳过")
            return True

        type_desc = "高频" if stock_type == "high" else ("低频" if stock_type == "low" else "默认")
        print(f"【条件8独立阈值执行】{symbol} 类型:{type_desc} 上涨阈值:{rise_thr*100:.2f}% 下跌阈值:{decline_thr*100:.2f}%")

        place_buy(symbol, current_price, qty, res["reason"], "condition8", res["trigger_data"],
                  order_ledger=order_ledger, session_registry=session_registry)
        day_data.condition8_trade_times += 1
        day_data.condition8_last_trade_price = current_price
        day_data.condition8_last_trigger_price = current_price
        day_data.condition8_total_buy_today = total_buy_today + qty

        if CONDITION8_MULTIPLE_ORDER_ENABLED and actual_multiple > 1:
            print(f"【条件8倍数委托执行】{symbol} 买入 {qty}股 (基础{base_qty}×倍数{actual_multiple}) "
                  f"跳过{skipped_grids}个网格{' [已达上限]' if hit_limit else ''}")
        return True