# service/order_status_service.py
# -*- coding: utf-8 -*-
"""
订单状态变更处理服务，从 event_handler 中抽离纯逻辑。
"""

from __future__ import annotations
import logging
from typing import Any

from domain.contexts.tick_context import TickContext
from repository.mail_sender import send_email
from service.pyramid_service import add_callback_task

logger = logging.getLogger(__name__)


def handle_order_filled(ctx: TickContext, order: dict[str, Any]) -> None:
    """处理订单完全成交（status == 3）"""
    from gm.api import get_execution_reports

    cl_ord_id = order.get("cl_ord_id")
    symbol = order.get("symbol")
    price = order.get("price", 0.0)
    volume = order.get("volume", 0)

    reports = get_execution_reports()
    exec_price = price
    exec_volume = volume
    for r in reports:
        if r.get("clOrdId") == cl_ord_id and r.get("execType") == 15:
            exec_price = r.get("price", price)
            exec_volume = r.get("volume", volume)
            break

    if exec_price > 0:
        ctx.condition8_tracker.record_condition8_done_price(symbol, exec_price)

    if order.get("side") == 2:
        pending_order = ctx.order_repo.get_pending_order(cl_ord_id)
        condition_type = pending_order.get("condition_type") if pending_order else None
        if condition_type in ['condition2', 'condition9', 'condition8', 'pyramid_profit']:
            board_status = ctx.board_repo.get_board_status(symbol)
            prev_close = board_status.prev_close if board_status else 0.0
            if prev_close > 0:
                sell_amount = exec_price * exec_volume
                task = add_callback_task(
                    symbol=symbol,
                    sell_price=exec_price,
                    prev_close=prev_close,
                    sell_amount=sell_amount,
                    sell_quantity=exec_volume,
                    condition_type=condition_type,
                    store=ctx.callback_store,
                    config=ctx.callback_config
                )
                if task:
                    send_email(
                        f"动态回调加仓任务创建-{symbol}",
                        f"股票:{symbol}\n来源:{condition_type}\n卖出价:{exec_price:.4f}\n"
                        f"昨日收:{prev_close:.4f}\n获利幅度:{task.callback_threshold*100:.2f}%\n"
                        f"触发价:{task.trigger_price:.4f}\n计划买入:{task.buy_quantity}股"
                    )

    ctx.condition8_tracker.cancel_condition8_opposite(symbol, cl_ord_id)


def handle_order_cancelled(ctx: TickContext, order: dict[str, Any]) -> None:
    """处理订单已撤销（status == 23）"""
    symbol = order.get("symbol")
    ctx.condition8_tracker.clear_condition8_state(symbol)
    ctx.cancel_lock_manager.mark_cancelled(symbol)