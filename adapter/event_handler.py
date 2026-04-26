# adapter/event_handler.py
# -*- coding: utf-8 -*-
"""
GM 事件薄转发层
不再持有全局单例，全部从 context.data 获取 TickContext。
"""
from __future__ import annotations
from datetime import datetime
from adapter.context_wrapper import ContextWrapper
from use_case.handle_tick import handle_tick
from use_case.handle_close import handle_market_close
from use_case.health_check import update_sleep_state
from repository.mail_sender import send_email
from domain.contexts.tick_context import TickContext
import pytz
import traceback

beijing_tz = pytz.timezone("Asia/Shanghai")

def _get_tick_ctx(context) -> TickContext:
    return context.data['tick_context']

def on_tick(context: Any, tick: dict[str, Any]) -> None:
    try:
        ctx = ContextWrapper(context)
        tick_ctx = _get_tick_ctx(context)
        current_sleep = tick_ctx.order_ledger.get_sleep_state()
        new_sleep = update_sleep_state(ctx.now(), current_sleep)
        if new_sleep != current_sleep:
            tick_ctx.order_ledger.set_sleep_state(new_sleep)
        if new_sleep:
            return

        handle_tick(tick, tick_ctx)
        tick_time = tick["created_at"].astimezone(beijing_tz)
        if (tick_time.hour == 15 and tick_time.minute >= 0) or tick_time.hour > 15:
            handle_market_close(tick["symbol"], tick_time,
                                tick_ctx.session_registry,
                                tick_ctx.board_repo,
                                tick_ctx.callback_store,
                                tick_ctx.order_ledger)
    except Exception as e:
        print(f"on_tick 异常: {e}")
        traceback.print_exc()
        send_email("策略异常-on_tick", str(e))

def on_error(context: Any, error_code: int, error_info: str) -> None:
    msg = f"策略错误: 错误代码={error_code}, 错误信息={error_info}"
    print(msg)
    traceback.print_exc()
    send_email("策略错误-on_error", msg)

def on_backtest_finished(context: Any, indicator: dict[str, Any]) -> None:
    print("回测结束")
    print(indicator)
    send_email("回测结束", str(indicator))

def on_order_status(context: Any, order: dict[str, Any]) -> None:
    try:
        tick_ctx = _get_tick_ctx(context)
        status = order.get("status")
        cl_ord_id = order.get("cl_ord_id")
        symbol = order.get("symbol")
        price = order.get("price", 0.0)
        volume = order.get("volume", 0)

        if status == 3:  # 已成
            from gm.api import get_execution_reports
            reports = get_execution_reports()
            exec_price = price
            exec_volume = volume
            for r in reports:
                if r.get("clOrdId") == cl_ord_id and r.get("execType") == 15:
                    exec_price = r.get("price", price)
                    exec_volume = r.get("volume", volume)
                    break

            if exec_price > 0:
                tick_ctx.order_ledger.record_condition8_done_price(symbol, exec_price)

            if order.get("side") == 2:
                pending_order = tick_ctx.order_ledger.get_pending_order(cl_ord_id)
                condition_type = pending_order.get("condition_type") if pending_order else None

                if condition_type in ['condition2', 'condition9', 'condition8', 'pyramid_profit']:
                    board_status = tick_ctx.board_repo.get_board_status(symbol)
                    prev_close = board_status.prev_close if board_status else 0.0
                    if prev_close > 0:
                        sell_amount = exec_price * exec_volume
                        from service.pyramid_service import add_callback_task
                        task = add_callback_task(
                            symbol=symbol, sell_price=exec_price, prev_close=prev_close,
                            sell_amount=sell_amount, sell_quantity=exec_volume,
                            condition_type=condition_type, store=tick_ctx.callback_store
                        )
                        if task:
                            send_email(
                                f"动态回调加仓任务创建-{symbol}",
                                f"股票:{symbol}\n来源:{condition_type}\n卖出价:{exec_price:.4f}\n"
                                f"昨日收:{prev_close:.4f}\n获利幅度:{task.callback_threshold*100:.2f}%\n"
                                f"触发价:{task.trigger_price:.4f}\n计划买入:{task.buy_quantity}股"
                            )

            tick_ctx.order_ledger.cancel_condition8_opposite(symbol, cl_ord_id)

        elif status == 23:  # 已撤
            tick_ctx.order_ledger.clear_condition8_state(symbol)
            tick_ctx.order_ledger.mark_cancelled(symbol)

    except Exception as e:
        print(f"on_order_status 异常: {e}")
        traceback.print_exc()
        send_email("策略异常-on_order_status", str(e))