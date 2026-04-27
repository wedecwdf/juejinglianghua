# service/execution/ma_executor.py
# -*- coding: utf-8 -*-
"""
MA均线相关交易执行器（条件4、5、6买入，条件7卖出）
Layer 6
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from domain.day_data import DayData
from domain.stores import SessionRegistry
from service.condition_service import check_condition4, check_condition5, check_condition6, check_condition7
from service.order_executor import place_buy, place_sell
from config.strategy import CONDITION8_MAX_TOTAL_QUANTITY

logger = logging.getLogger(__name__)

def execute_ma_trading(symbol: str, current_price: float, day_data: DayData,
                       available_position: int, tick_time: datetime,
                       session_registry: SessionRegistry) -> bool:
    context = session_registry.get_condition4_7(symbol)
    total_buy = session_registry.get_total_buy_quantity(symbol)
    max_total = CONDITION8_MAX_TOTAL_QUANTITY.get(symbol, 0)

    for cond_fn, name in [(check_condition4, "condition4"),
                          (check_condition5, "condition5"),
                          (check_condition6, "condition6")]:
        res = cond_fn(day_data, context, current_price)
        if res:
            if total_buy + res["quantity"] > max_total:
                logger.info("[MA] %s 累计买入%d+%d将超过上限%d，跳过",
                            symbol, total_buy, res["quantity"], max_total)
                return True
            place_buy(symbol, current_price, res["quantity"],
                      res["reason"], name, res["trigger_data"],
                      session_registry=session_registry)
            setattr(context, f'buy_{name}_triggered', True)
            session_registry.set_total_buy_quantity(symbol, total_buy + res["quantity"])
            logger.info("【MA执行】%s %s 买入 %d股 @ %.4f", symbol, name, res["quantity"], current_price)
            return True

    res = check_condition7(day_data, context, current_price, tick_time)
    if res and total_buy > 0:
        place_sell(symbol, current_price - res["sell_price_offset"], total_buy,
                   res["reason"], "condition7", res["trigger_data"],
                   session_registry=session_registry)
        context.condition7_triggered = True
        session_registry.reset_total_buy(symbol)
        logger.info("【MA执行】%s 条件7卖出 %d股 @ %.4f", symbol, total_buy, current_price - res["sell_price_offset"])
        return True
    return False