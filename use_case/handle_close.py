# use_case/handle_close.py
# -*- coding: utf-8 -*-
"""
收盘处理：打印、独立落库。
不再依赖 config.strategy 旧常量，通过 context_store 获取条件状态。
"""
from __future__ import annotations
import logging
import os
from datetime import datetime
from domain.stores import SessionRegistry, BoardStateRepository, CallbackTaskStore
from domain.stores.order_interfaces import OrderRepository
from domain.stores.context_store import ContextStore

logger = logging.getLogger(__name__)

# 从环境变量读取启用标志，提供默认值
DYNAMIC_PROFIT_NEXT_DAY_ADJUST_ENABLED = os.getenv('DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED', 'true').lower() == 'true'
CALLBACK_ADDITION_ENABLED = os.getenv('CALLBACK_ADDITION_ENABLED', 'true').lower() == 'true'
PYRAMID_PROFIT_ENABLED = os.getenv('PYRAMID_PROFIT_ENABLED', 'true').lower() == 'true'


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

    # 通过 context_store 获取条件4-7状态
    try:
        ctx47 = context_store.get('condition4_7', symbol)
        logger.info("条件4买入: %s", '已触发' if ctx47.buy_condition4_triggered else '未触发')
        logger.info("条件5买入: %s", '已触发' if ctx47.buy_condition5_triggered else '未触发')
        logger.info("条件6买入: %s", '已触发' if ctx47.buy_condition6_triggered else '未触发')
        logger.info("条件7卖出: %s", '已触发' if ctx47.condition7_triggered else '未触发')
    except KeyError:
        logger.info("条件4-7状态未初始化")

    # 条件8状态
    try:
        ctx8 = context_store.get('condition8', symbol)
        logger.info("条件8交易次数: %d/10", ctx8.condition8_trade_times)
        logger.info("条件8状态: %s", '休眠' if ctx8.condition8_sleeping else '活跃')
    except KeyError:
        logger.info("条件8状态未初始化")

    # 条件2状态
    try:
        ctx2 = context_store.get('condition2', symbol)
        logger.info("条件2动态止盈: %s, 卖出次数: %d",
                    '已触发' if ctx2.dynamic_profit_triggered else '未触发',
                    ctx2.dynamic_profit_sell_times)
    except KeyError:
        logger.info("条件2状态未初始化")

    # 条件9状态
    try:
        ctx9 = context_store.get('condition9', symbol)
        logger.info("条件9动态止盈: %s, 卖出次数: %d",
                    '已触发' if ctx9.condition9_triggered else '未触发',
                    ctx9.condition9_sell_times)
        logger.info("条件9停止监测: %s", '是' if ctx9.condition9_stopped else '否')
    except KeyError:
        logger.info("条件9状态未初始化")

    # 板数打印
    bcd = board_repo.get_board_count_data(symbol)
    if bcd:
        logger.info("板数: 第%d板 首板日期:%s 昨收:%.2f 涨停价:%.2f",
                    bcd.count, bcd.start_date, bcd.prev_close, bcd.limit_up_price)
    else:
        logger.info("板数: 未涨停")

    # 动态回调加仓任务
    if CALLBACK_ADDITION_ENABLED:
        task_data = callback_store.get_task(symbol)
        if task_data:
            is_active = task_data.get('is_active', False)
            status_str = "活跃" if is_active else "已失效"
            logger.info("动态回调加仓任务: 1个 [%s]", status_str)
            logger.info(" 任务详情: 卖出价=%.4f, 昨收=%.4f, 获利幅度=%.2f%%, 触发价=%.4f, 计划买入=%d股, 来源=%s",
                        task_data.get('sell_price', 0), task_data.get('prev_close', 0),
                        task_data.get('callback_threshold', 0) * 100, task_data.get('trigger_price', 0),
                        task_data.get('buy_quantity', 0), task_data.get('condition_type', '未知'))
        else:
            logger.info("动态回调加仓任务: 无")
    else:
        logger.info("动态回调加仓: 已禁用")

    # 金字塔止盈
    if PYRAMID_PROFIT_ENABLED:
        try:
            pyr_ctx = context_store.get('pyramid', symbol)
            triggered_levels = [i + 1 for i, s in enumerate(pyr_ctx.pyramid_profit_status) if s]
            logger.info("金字塔止盈: 已触发级别 %s", triggered_levels if triggered_levels else '无')
            logger.info(" 独立基准价: %.4f", pyr_ctx.pyramid_profit_base_price)
            logger.info(" 独立触发状态: %s", '已触发' if pyr_ctx.pyramid_profit_triggered else '未触发')
        except KeyError:
            logger.info("金字塔止盈状态未初始化")
    else:
        logger.info("金字塔止盈: 已禁用")

    # 次日调整机制
    if DYNAMIC_PROFIT_NEXT_DAY_ADJUST_ENABLED:
        try:
            adj_ctx = context_store.get('next_day', symbol)
            if adj_ctx.data.get("enabled", False):
                logger.info("动态止盈次日调整机制: 已启用")
                logger.info(" 止损价: %.4f", adj_ctx.data.get('stop_loss_price', 0))
                logger.info(" 卖出比例: %.0f%%", adj_ctx.data.get('sell_ratio', 0) * 100)
                logger.info(" 延续天数: %d", adj_ctx.data.get('days_count', 0))
            else:
                logger.info("动态止盈次日调整机制: 未启用")
        except KeyError:
            logger.info("动态止盈次日调整机制: 未初始化")
    else:
        logger.info("动态止盈次日调整机制: 已禁用")

    # 持久化
    order_repo.save()
    board_repo.save()
    callback_store.save()
    session_registry.save()
    logger.info("===== %s 收盘处理完成 =====", symbol)