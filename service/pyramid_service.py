# service/pyramid_service.py
# -*- coding: utf-8 -*-
"""
动态回调加仓服务（替代原金字塔加仓服务）
"""
from __future__ import annotations
from typing import Optional, Dict, Any, List
from datetime import datetime
from domain.base_price import CallbackAdditionTask, calculate_trigger_prices, calculate_callback_buy_quantity
from config.strategy import (
    CALLBACK_ADDITION_ENABLED,
    CALLBACK_ON_CONDITION2,
    CALLBACK_ON_CONDITION9,
    CALLBACK_ON_CONDITION8,
    MIN_TRADE_UNIT
)
from domain.stores import CallbackTaskStore

VALID_CALLBACK_CONDITIONS = {
    'condition2': CALLBACK_ON_CONDITION2,
    'condition9': CALLBACK_ON_CONDITION9,
    'condition8': CALLBACK_ON_CONDITION8,
    'condition8_pyramid_profit': CALLBACK_ON_CONDITION8,
}

def should_create_callback_task(condition_type: str) -> bool:
    if not CALLBACK_ADDITION_ENABLED:
        return False
    if condition_type in ['board_dynamic_profit', 'board_break', 'board_break_static', 'board_break_dynamic']:
        return False
    return VALID_CALLBACK_CONDITIONS.get(condition_type, False)

def add_callback_task(symbol: str, sell_price: float, prev_close: float,
                      sell_amount: float, sell_quantity: int, condition_type: str,
                      store: Optional[CallbackTaskStore] = None) -> Optional[CallbackAdditionTask]:
    if not should_create_callback_task(condition_type):
        return None
    if prev_close <= 0 or sell_price <= 0 or sell_amount <= 0:
        print(f"【动态回调加仓】{symbol} 参数无效，跳过任务创建")
        return None

    if store is None:
        store = CallbackTaskStore()

    old_task_data = store.get_task(symbol)
    if old_task_data and old_task_data.get('is_active'):
        old_task = CallbackAdditionTask.from_dict(old_task_data)
        print(f"【动态回调加仓-任务覆盖】{symbol} 旧任务被强制废止: "
              f"旧基准价={old_task.sell_price:.4f}, "
              f"旧回调阈值={old_task.callback_threshold*100:.2f}%, "
              f"旧来源={old_task.condition_type}")
        print(f"【动态回调加仓-任务覆盖】{symbol} 新任务覆盖: "
              f"新基准价={sell_price:.4f}, "
              f"新来源={condition_type}")

    task = CallbackAdditionTask(
        sell_price=sell_price, prev_close=prev_close,
        sell_amount=sell_amount, sell_quantity=sell_quantity,
        condition_type=condition_type
    )

    if task.buy_quantity < MIN_TRADE_UNIT:
        print(f"【动态回调加仓】{symbol} 折算股数{task.buy_quantity}低于最小单位{MIN_TRADE_UNIT}，任务自动终止。"
              f"卖出金额={sell_amount:.2f}, 触发价={task.trigger_price:.4f}")
        task.is_active = False

    store.set_task(symbol, task.to_dict())
    store.save()

    if task.is_active:
        print(f"【动态回调加仓-任务创建】{symbol} "
              f"基准价={sell_price:.4f}, 昨日收={prev_close:.4f}, "
              f"获利幅度R={task.callback_threshold*100:.2f}%, "
              f"触发价={task.trigger_price:.4f}, 计划买入={task.buy_quantity}股, 来源={condition_type}")
    return task

def check_callback_strategy(symbol: str, current_price: float,
                            store: Optional[CallbackTaskStore] = None) -> Optional[Dict[str, Any]]:
    if not CALLBACK_ADDITION_ENABLED:
        return None
    if store is None:
        store = CallbackTaskStore()

    task_data = store.get_task(symbol)
    if not task_data:
        return None

    task = CallbackAdditionTask.from_dict(task_data)
    if not task.is_active:
        return None

    if task.is_triggered(current_price):
        print(f"【动态回调加仓-触发】{symbol} 当前价={current_price:.4f} <= 触发价={task.trigger_price:.4f}, "
              f"获利幅度R={task.callback_threshold*100:.2f}%, 计划买入={task.buy_quantity}股, 来源={task.condition_type}")
        return {
            'quantity': task.buy_quantity,
            'trigger_price': task.trigger_price,
            'reason': f"动态回调加仓触发({task.condition_type})",
            'condition_type': task.condition_type,
            'task': task,
            'trigger_data': {
                'pre_task_state': task.to_dict(),
                'sell_price': task.sell_price,
                'prev_close': task.prev_close,
                'callback_threshold': task.callback_threshold,
                'trigger_price': task.trigger_price,
            }
        }
    return None

def complete_callback_task(symbol: str, store: Optional[CallbackTaskStore] = None) -> None:
    if store is None:
        store = CallbackTaskStore()
    task_data = store.get_task(symbol)
    if task_data:
        task = CallbackAdditionTask.from_dict(task_data)
        task.complete()
        store.set_task(symbol, task.to_dict())
        store.save()
        print(f"【动态回调加仓-完成】{symbol} 任务已完成并标记失效")

def remove_callback_task(symbol: str, condition_type: Optional[str] = None,
                         store: Optional[CallbackTaskStore] = None) -> bool:
    if store is None:
        store = CallbackTaskStore()
    task_data = store.get_task(symbol)
    if not task_data:
        return False
    if condition_type and task_data.get('condition_type') != condition_type:
        return False
    task = CallbackAdditionTask.from_dict(task_data)
    task.is_active = False
    store.set_task(symbol, task.to_dict())
    store.save()
    print(f"【动态回调加仓-移除】{symbol} 任务已被移除/废止")
    return True

def get_callback_task(symbol: str, store: Optional[CallbackTaskStore] = None) -> Optional[CallbackAdditionTask]:
    if store is None:
        store = CallbackTaskStore()
    task_data = store.get_task(symbol)
    if task_data:
        task = CallbackAdditionTask.from_dict(task_data)
        if task.is_active:
            return task
    return None

def get_all_active_tasks(store: Optional[CallbackTaskStore] = None) -> Dict[str, CallbackAdditionTask]:
    if store is None:
        store = CallbackTaskStore()
    active_tasks = {}
    for symbol, task_data in store.all_tasks().items():
        if task_data.get('is_active'):
            active_tasks[symbol] = CallbackAdditionTask.from_dict(task_data)
    return active_tasks