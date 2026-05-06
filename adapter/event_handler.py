# adapter/event_handler.py
# -*- coding: utf-8 -*-
"""
GM 事件薄转发层，使用拆分后的小接口，直接调用服务函数。
"""

from __future__ import annotations
import logging
from datetime import datetime

from use_case.handle_tick import handle_tick
from use_case.handle_close import handle_market_close
from use_case.health_check import update_sleep_state
from repository.mail_sender import send_email
from domain.contexts.tick_context import TickContext
from service.order_status_service import handle_order_filled, handle_order_cancelled
import pytz
import traceback

beijing_tz = pytz.timezone("Asia/Shanghai")
logger = logging.getLogger(__name__)


def on_tick(context: Any, tick: dict[str, Any]) -> None:
    try:
        tick_ctx: TickContext = context.tick_ctx
        current_sleep = tick_ctx.sleep_state_manager.get_sleep_state()
        new_sleep = update_sleep_state(context.now, current_sleep)
        if new_sleep != current_sleep:
            tick_ctx.sleep_state_manager.set_sleep_state(new_sleep)
        if new_sleep:
            return

        handle_tick(tick, tick_ctx)

        tick_time = tick["created_at"].astimezone(beijing_tz)
        if (tick_time.hour == 15 and tick_time.minute >= 0) or tick_time.hour > 15:
            handle_market_close(
                tick["symbol"], tick_time,
                tick_ctx.session_registry,
                tick_ctx.board_repo,
                tick_ctx.callback_store,
                tick_ctx.order_repo,
            )
    except Exception as e:
        logger.exception("on_tick 异常")
        send_email("策略异常-on_tick", str(e))


def on_error(context: Any, error_code: int, error_info: str) -> None:
    msg = f"策略错误: 错误代码={error_code}, 错误信息={error_info}"
    logger.error(msg)
    traceback.print_exc()
    send_email("策略错误-on_error", msg)


def on_backtest_finished(context: Any, indicator: dict[str, Any]) -> None:
    logger.info("回测结束")
    logger.info(indicator)
    send_email("回测结束", str(indicator))


def on_order_status(context: Any, order: dict[str, Any]) -> None:
    try:
        tick_ctx: TickContext = context.tick_ctx
        status = order.get("status")

        if status == 3:   # 已成
            handle_order_filled(tick_ctx, order)
        elif status == 23:  # 已撤
            handle_order_cancelled(tick_ctx, order)

    except Exception as e:
        logger.exception("on_order_status 异常")
        send_email("策略异常-on_order_status", str(e))