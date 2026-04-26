# use_case/handle_close.py
# -*- coding: utf-8 -*-
"""
收盘处理：打印、独立落库
"""
from __future__ import annotations
import os
from datetime import datetime
from domain.stores import SessionRegistry, BoardStateRepository, CallbackTaskStore, OrderLedger
from config.strategy import (
    DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED,
    CALLBACK_ADDITION_ENABLED,
    PYRAMID_PROFIT_ENABLED,
    PYRAMID_TOTAL_QUANTITY,
    HIGH_FREQUENCY_STOCKS,
    LOW_FREQUENCY_STOCKS,
)

def handle_market_close(symbol: str, tick_time: datetime,
                        session_registry: SessionRegistry,
                        board_repo: BoardStateRepository,
                        callback_store: CallbackTaskStore,
                        order_ledger: OrderLedger) -> None:
    if tick_time.hour < 15:
        return

    day_data = session_registry.get(symbol)
    if not day_data or day_data.date != tick_time.date():
        return

    print(f"\n===== {symbol} 收盘处理开始 =====")
    print(f"当日买入总量: {session_registry.get_total_buy_quantity(symbol)}股")
    print(f"条件4买入: {'已触发' if day_data.buy_condition4_triggered else '未触发'}")
    print(f"条件5买入: {'已触发' if day_data.buy_condition5_triggered else '未触发'}")
    print(f"条件6买入: {'已触发' if day_data.buy_condition6_triggered else '未触发'}")
    print(f"条件7卖出: {'已触发' if day_data.condition7_triggered else '未触发'}")
    print(f"条件8交易次数: {day_data.condition8_trade_times}/10")
    print(f"条件8状态: {'休眠' if day_data.condition8_sleeping else '活跃'}")
    print(f"条件2动态止盈: {'已触发' if day_data.dynamic_profit_triggered else '未触发'}, 卖出次数: {day_data.dynamic_profit_sell_times}")
    print(f"条件9动态止盈: {'已触发' if day_data.condition9_triggered else '未触发'}, 卖出次数: {day_data.condition9_sell_times}")
    print(f"条件9停止监测: {'是' if day_data.condition9_stopped else '否'}")
    print(f"条件互斥状态: {'条件2已触发，禁止条件9' if day_data.condition2_triggered_and_sold else '正常'}")

    bcd = board_repo.get_board_count_data(symbol)
    if bcd:
        print(f"板数: 第{bcd.count}板 首板日期:{bcd.start_date} 昨收:{bcd.prev_close:.2f} 涨停价:{bcd.limit_up_price:.2f}")
    else:
        print("板数: 未涨停")

    if CALLBACK_ADDITION_ENABLED:
        task_data = callback_store.get_task(symbol)
        if task_data:
            is_active = task_data.get('is_active', False)
            status_str = "活跃" if is_active else "已失效"
            print(f"动态回调加仓任务: 1个 [{status_str}]")
            print(f" 任务详情: 卖出价={task_data.get('sell_price', 0):.4f}, 昨收={task_data.get('prev_close', 0):.4f}, "
                  f"获利幅度={task_data.get('callback_threshold', 0)*100:.2f}%, "
                  f"触发价={task_data.get('trigger_price', 0):.4f}, 计划买入={task_data.get('buy_quantity', 0)}股, "
                  f"来源={task_data.get('condition_type', '未知')}")
        else:
            print("动态回调加仓任务: 无")
    else:
        print("动态回调加仓: 已禁用")

    if PYRAMID_PROFIT_ENABLED:
        status = day_data.pyramid_profit_status
        triggered_levels = [i + 1 for i, s in enumerate(status) if s]
        total_qty = PYRAMID_TOTAL_QUANTITY.get(symbol, 0)
        stock_type = "高频" if symbol in HIGH_FREQUENCY_STOCKS else ("低频" if symbol in LOW_FREQUENCY_STOCKS else "默认")
        print(f"【独立机制】金字塔止盈: 已触发级别 {triggered_levels if triggered_levels else '无'}")
        print(f" 股票类别: {stock_type}")
        print(f" 该股票独立配置的总卖出数量: {total_qty}股")
        print(f" 独立基准价: {day_data.pyramid_profit_base_price:.4f}")
        print(f" 独立触发状态: {'已触发' if day_data.pyramid_profit_triggered else '未触发'}")
    else:
        print("金字塔止盈: 已禁用")

    if DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_ENABLED:
        adj = day_data.dynamic_profit_next_day_adjustment
        if adj.get("enabled", False):
            print(f"动态止盈次日调整机制: 已启用")
            print(f" 止损价: {adj.get('stop_loss_price', 0):.4f}")
            print(f" 卖出比例: {adj.get('sell_ratio', 0)*100}%")
            print(f" 延续天数: {adj.get('days_count', 0)}")
        else:
            print("动态止盈次日调整机制: 未启用")

    # 各仓库独立保存
    order_ledger.save()
    board_repo.save()
    callback_store.save()
    session_registry.save()
    print(f"===== {symbol} 收盘处理完成 =====")