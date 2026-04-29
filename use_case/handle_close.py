# use_case/handle_close.py
# -*- coding: utf-8 -*-
"""
收盘处理，通过 ContextStore 获取条件状态。
"""
from __future__ import annotations
import logging
import os
from datetime import datetime
from domain.stores import SessionRegistry, BoardStateRepository, CallbackTaskStore
from domain.stores.order_interfaces import OrderRepository
from domain.stores.context_store import ContextStore
from config.strategy import (
    DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED,
    CALLBACK_ADDITION_ENABLED,
    PYRAMID_PROFIT_ENABLED,
)

logger = logging.getLogger(__name__)


def handle_market_close(symbol: str, tick_time: datetime,
                        session_registry: SessionRegistry,
                        board_repo: BoardStateRepository,
                        callback_store: CallbackTaskStore,
                        order_repo: OrderRepository,
                        context_store: ContextStore) -> None:
    if tick_time.hour < 15:
        return

    day_data = session_registry.get(symbol)
    if not day_data or day_data.date != tick_time.date():
        return

    logger.info("===== %s 收盘处理开始 =====", symbol)
    logger.info("当日买入总量: %d股", session_registry.get_total_buy_quantity(symbol))

    try:
        ctx47 = context_store.get('condition4_7', symbol)
        logger.info("条件4买入: %s", '已触发' if ctx47.buy_condition4_triggered else '未触发')
        logger.info("条件5买入: %s", '已触发' if ctx47.buy_condition5_triggered else '未触发')
        logger.info("条件6买入: %s", '已触发' if ctx47.buy_condition6_triggered else '未触发')
        logger.info("条件7卖出: %s", '已触发' if ctx47.condition7_triggered else '未触发')
    except KeyError:
        logger.info("条件4-7状态未初始化")

    try:
        ctx8 = context_store.get('condition8', symbol)
        logger.info("条件8交易次数: %d/10", ctx8.condition8_trade_times)
        logger.info("条件8状态: %s", '休眠' if ctx8.condition8_sleeping else '活跃')
    except KeyError:
        logger.info("条件8状态未初始化")

    try:
        ctx2 = context_store.get('condition2', symbol)
        logger.info("条件2动态止盈: %s, 卖出次数: %d",
                    '已触发' if ctx2.dynamic_profit_triggered else '未触发', ctx2.dynamic_profit_sell_times)
    except KeyError:
        logger.info("条件2状态未初始化")

    try:
        ctx9 = context_store.get('condition9', symbol)
        logger.info("条件9动态止盈: %s, 卖出次数: %d",
                    '已触发' if ctx9.condition9_triggered else '未触发', ctx9.condition9_sell_times)
    except KeyError:
        logger.info("条件9状态未初始化")

    bcd = board_repo.get_board_count_data(symbol)
    if bcd:
        logger.info("板数: 第%d板 首板日期:%s 昨收:%.2f 涨停价:%.2f",
                    bcd.count, bcd.start_date, bcd.prev_close, bcd.limit_up_price)
    else:
        logger.info("板数: 未涨停")

    if CALLBACK_ADDITION_ENABLED:
        task_data = callback_store.get_task(symbol)
        if task_data:
            is_active = task_data.get('is_active', False)
            status_str = "活跃" if is_active else "已失效"
            logger.info("动态回调加仓任务: 1个 [%s]", status_str)
        else:
            logger.info("动态回调加仓任务: 无")
    else:
        logger.info("动态回调加仓: 已禁用")

    if PYRAMID_PROFIT_ENABLED:
        try:
            pyr_ctx = context_store.get('pyramid', symbol)
            logger.info("金字塔止盈: 已触发级别 %s",
                        [i+1 for i, s in enumerate(pyr_ctx.pyramid_profit_status) if s] or '无')
        except KeyError:
            logger.info("金字塔止盈状态未初始化")
    else:
        logger.info("金字塔止盈: 已禁用")

    order_repo.save()
    board_repo.save()
    callback_store.save()
    session_registry.save()
    logger.info("===== %s 收盘处理完成 =====", symbol)