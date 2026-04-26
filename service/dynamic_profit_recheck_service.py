# -*- coding: utf-8 -*-
"""
动态止盈撤单后重新判定服务

实现规范：
1. 触发时机：撤单后的下一个tick，常规流程前优先执行
2. 前置状态校验：原监控状态、卖出次数、持仓检查
3. 优先级互斥：条件2优先于条件9，条件2触发时强制清理条件9状态
4. 价格状态分支：跌破止盈线（卖出）、反弹未创新高（维持）、反弹创新高（更新止盈线）
5. 部分成交防护：卖出数量不超过可用持仓
6. 与次日调整机制隔离：不修改次日调整机制数据
7. 防重复标记：设置post_cancel_rechecked防止本次tick常规流程重复处理
"""

from __future__ import annotations
from typing import Optional, Dict, Any, Tuple

from domain.day_data import DayData
from repository.state_gateway import StateGateway
from service.order_executor import place_sell, sell_qty_by_percent

from config.strategy import (
    # 条件2配置
    MAX_DYNAMIC_PROFIT_SELL_TIMES,
    CONDITION2_DECLINE_PERCENT,
    CONDITION2_DYNAMIC_LINE_THRESHOLD,
    CONDITION2_SELL_PERCENT_HIGH,
    CONDITION2_SELL_PERCENT_LOW,
    CONDITION2_SELL_PRICE_OFFSET,
    # 条件9配置
    MAX_CONDITION9_SELL_TIMES,
    CONDITION9_DECLINE_PERCENT,
    CONDITION9_DYNAMIC_LINE_THRESHOLD,
    CONDITION9_SELL_PERCENT_HIGH,
    CONDITION9_SELL_PERCENT_LOW,
    CONDITION9_SELL_PRICE_OFFSET,
)


def execute_post_cancel_recheck(
        symbol: str,
        current_price: float,
        available_position: int,
        day_data: DayData,
        base_price: float,
        board_break_active: bool = False
) -> Tuple[bool, bool]:
    """
    执行撤单后的动态止盈重新判定（规范实现）

    Args:
        symbol: 股票代码
        current_price: 当前价格
        available_position: 可用持仓
        day_data: 日线数据
        base_price: 基准价（开盘价）
        board_break_active: 炸板动态止盈是否激活

    Returns:
        (condition2_processed, condition9_processed): 表示是否处理了对应条件（无论是否卖出）
    """
    c2_processed = False
    c9_processed = False

    # 优先处理条件2（规范第3条：优先级互斥）
    if day_data.condition2_recheck_after_cancel:
        c2_processed = _recheck_condition2(
            symbol, current_price, available_position, day_data, base_price, board_break_active
        )

        if c2_processed:
            # 规范第3条：条件2满足重新触发条件，强制清理条件9状态
            if day_data.condition9_triggered:
                day_data.condition9_triggered = False
                day_data.condition9_high_price = -float('inf')
                day_data.condition9_profit_line = -float('inf')
                print(f"【优先级覆盖】{symbol} 条件2重新判定处理，清理条件9触发状态")

            # 清理recheck标记（已处理完成）
            day_data.condition2_recheck_after_cancel = False

            # 条件2已处理，条件9本次不再参与重新判定（规范第3条）
            return c2_processed, False

    # 处理条件9（仅当条件2未处理时）
    if not c2_processed and day_data.condition9_recheck_after_cancel:
        c9_processed = _recheck_condition9(
            symbol, current_price, available_position, day_data, base_price, board_break_active
        )

        if c9_processed:
            day_data.condition9_recheck_after_cancel = False

    return c2_processed, c9_processed


def _recheck_condition2(
        symbol: str,
        current_price: float,
        available_position: int,
        day_data: DayData,
        base_price: float,
        board_break_active: bool
) -> bool:
    """
    重新判定条件2（规范第4条实现）

    Returns:
        bool: 是否进行了处理（无论是否卖出）
    """
    # 规范第2条：前置状态校验
    if not day_data.dynamic_profit_triggered:
        return False

    if day_data.dynamic_profit_sell_times >= MAX_DYNAMIC_PROFIT_SELL_TIMES:
        return False

    if available_position <= 0:
        return False

    if board_break_active:
        return False

    # 获取当前状态
    profit_line = day_data.dynamic_profit_line
    high_price = day_data.dynamic_profit_high_price

    # 规范第4.1条：跌破止盈线情形
    if current_price <= profit_line:
        # 计算卖出比例（与常规逻辑一致）
        dynamic_line_increase = (profit_line - base_price) / base_price if base_price > 0 else 0
        sell_percent = (CONDITION2_SELL_PERCENT_HIGH
                        if dynamic_line_increase >= CONDITION2_DYNAMIC_LINE_THRESHOLD
                        else CONDITION2_SELL_PERCENT_LOW)

        # 规范第5条：部分成交防护
        sell_qty = sell_qty_by_percent(available_position, sell_percent)
        if sell_qty > available_position:
            sell_qty = (available_position // 100) * 100
            print(f"【条件2重新判定-部分成交防护】{symbol} 计划卖出数量超过可用持仓，调整为{sell_qty}股")

        if sell_qty > 0:
            place_sell(
                symbol=symbol,
                price=current_price - CONDITION2_SELL_PRICE_OFFSET,
                quantity=sell_qty,
                reason="条件2动态止盈撤单后重新判定-跌破止盈线",
                condition_type="condition2",
                trigger_data={
                    'pre_trigger_state': True,
                    'pre_high_price': high_price,
                    'pre_profit_line': profit_line,
                    'pre_sell_count': day_data.dynamic_profit_sell_times,
                    'recheck_scenario': 'break_line',
                    'is_post_cancel_recheck': True  # 标记为撤单后重新判定
                }
            )

            # 更新状态
            day_data.dynamic_profit_sell_times += 1
            day_data.total_sell_times += 1
            day_data.condition2_triggered_and_sold = True

            print(f"【条件2重新判定】{symbol} 跌破止盈线（{profit_line:.4f}），执行卖出 {sell_qty}股")

        # 规范第4.1条：设置防重复标记
        day_data.condition2_post_cancel_rechecked = True
        return True

    # 规范第4.3条：反弹创新高情形
    elif current_price > high_price:
        # 更新最高价和止盈线
        day_data.dynamic_profit_high_price = current_price
        day_data.dynamic_profit_line = current_price * (1 - CONDITION2_DECLINE_PERCENT)

        day_data.condition2_post_cancel_rechecked = True
        print(
            f"【条件2重新判定】{symbol} 反弹创新高（{current_price:.4f}），更新止盈线至 {day_data.dynamic_profit_line:.4f}")
        return True

    # 规范第4.2条：反弹未创新高情形（profit_line < current_price <= high_price）
    else:
        # 维持现有监控状态不变
        day_data.condition2_post_cancel_rechecked = True
        print(
            f"【条件2重新判定】{symbol} 反弹未创新高（当前:{current_price:.4f}, 最高:{high_price:.4f}, 止盈线:{profit_line:.4f}），维持监控")
        return True


def _recheck_condition9(
        symbol: str,
        current_price: float,
        available_position: int,
        day_data: DayData,
        base_price: float,
        board_break_active: bool
) -> bool:
    """
    重新判定条件9（规范第4条实现）

    Returns:
        bool: 是否进行了处理（无论是否卖出）
    """
    # 规范第2条：前置状态校验
    if not day_data.condition9_triggered:
        return False

    if day_data.condition9_sell_times >= MAX_CONDITION9_SELL_TIMES:
        return False

    if available_position <= 0:
        return False

    if board_break_active:
        return False

    # 获取当前状态
    profit_line = day_data.condition9_profit_line
    high_price = day_data.condition9_high_price

    # 规范第4.1条：跌破止盈线情形
    if current_price <= profit_line:
        # 计算卖出比例
        dynamic_line_increase = (profit_line - base_price) / base_price if base_price > 0 else 0
        sell_percent = (CONDITION9_SELL_PERCENT_HIGH
                        if dynamic_line_increase >= CONDITION9_DYNAMIC_LINE_THRESHOLD
                        else CONDITION9_SELL_PERCENT_LOW)

        # 规范第5条：部分成交防护
        sell_qty = sell_qty_by_percent(available_position, sell_percent)
        if sell_qty > available_position:
            sell_qty = (available_position // 100) * 100
            print(f"【条件9重新判定-部分成交防护】{symbol} 计划卖出数量超过可用持仓，调整为{sell_qty}股")

        if sell_qty > 0:
            place_sell(
                symbol=symbol,
                price=current_price - CONDITION9_SELL_PRICE_OFFSET,
                quantity=sell_qty,
                reason="条件9动态止盈撤单后重新判定-跌破止盈线",
                condition_type="condition9",
                trigger_data={
                    'pre_trigger_state': True,
                    'pre_high_price': high_price,
                    'pre_profit_line': profit_line,
                    'pre_sell_count': day_data.condition9_sell_times,
                    'recheck_scenario': 'break_line',
                    'is_post_cancel_recheck': True
                }
            )

            # 更新状态
            day_data.condition9_sell_times += 1
            day_data.total_sell_times += 1

            print(f"【条件9重新判定】{symbol} 跌破止盈线（{profit_line:.4f}），执行卖出 {sell_qty}股")

        # 规范第4.1条：设置防重复标记
        day_data.condition9_post_cancel_rechecked = True
        return True

    # 规范第4.3条：反弹创新高情形
    elif current_price > high_price:
        day_data.condition9_high_price = current_price
        day_data.condition9_profit_line = current_price * (1 - CONDITION9_DECLINE_PERCENT)

        day_data.condition9_post_cancel_rechecked = True
        print(
            f"【条件9重新判定】{symbol} 反弹创新高（{current_price:.4f}），更新止盈线至 {day_data.condition9_profit_line:.4f}")
        return True

    # 规范第4.2条：反弹未创新高情形
    else:
        day_data.condition9_post_cancel_rechecked = True
        print(
            f"【条件9重新判定】{symbol} 反弹未创新高（当前:{current_price:.4f}, 最高:{high_price:.4f}, 止盈线:{profit_line:.4f}），维持监控")
        return True