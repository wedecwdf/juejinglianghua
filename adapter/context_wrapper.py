# adapter/context_wrapper.py
# -*- coding: utf-8 -*-

"""
统一封装 gm.api，方便 mock
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Dict, Optional

from gm.api import (
    subscribe as gm_subscribe,
    history as gm_history,
    get_position as gm_get_position,
    get_cash as gm_get_cash,
    get_orders as gm_get_orders,
    order_cancel as gm_order_cancel,
    order_volume as gm_order_volume,
    get_trading_dates as gm_get_trading_dates,
    PositionSide_Long
)


class ContextWrapper:
    """薄封装，所有 gm.api 调用都走这里"""

    def __init__(self, context: Any) -> None:
        self.ctx = context

    # -------------------- 行情 --------------------

    def subscribe(self, symbols: List[str], frequency: str, count: int, wait_group: bool = False) -> None:
        gm_subscribe(symbols=symbols, frequency=frequency, count=count, wait_group=wait_group)

    def history(self, symbol: str, frequency: str, start_time: str, end_time: str,
                fields: str = "", adjust: int = 0, df: bool = False) -> Any:
        return gm_history(symbol=symbol, frequency=frequency,
                          start_time=start_time, end_time=end_time,
                          fields=fields, adjust=adjust, df=df)

    # -------------------- 账户 --------------------

    def get_position(self) -> List[Dict[str, Any]]:
        return gm_get_position()

    def get_cash(self) -> Dict[str, Any]:
        return gm_get_cash()

    def get_orders(self) -> List[Dict[str, Any]]:
        return gm_get_orders()

    def order_cancel(self, cl_ord_id: str) -> None:
        gm_order_cancel(wait_cancel_orders=[{"cl_ord_id": cl_ord_id}])

    def order_volume(self, symbol: str, volume: int, side: int,
                     order_type: int, position_effect: int, price: float) -> Optional[str]:
        orders = gm_order_volume(symbol=symbol, volume=volume, side=side,
                                 order_type=order_type, position_effect=position_effect,
                                 price=price)
        return orders[0]["cl_ord_id"] if orders else None

    def get_trading_dates(self, start_date: str, end_date: str) -> List[str]:
        return gm_get_trading_dates(exchange="SHSE", start_date=start_date, end_date=end_date)

    # -------------------- 其他 --------------------

    def now(self) -> datetime:
        return self.ctx.now