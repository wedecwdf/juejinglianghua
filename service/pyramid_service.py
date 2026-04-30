# service/pyramid_service.py
# -*- coding: utf-8 -*-
"""
动态回调加仓服务，移除对旧全局常量的依赖，改用配置对象。
"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from domain.base_price import CallbackAdditionTask
from config.strategy.config_objects import CallbackAddConfig
from domain.stores.base import AbstractCallbackTaskStore

logger = logging.getLogger(__name__)

# 使用配置默认值替代旧常量
_callback_config = CallbackAddConfig()

VALID_CALLBACK_CONDITIONS = {
    'condition2': _callback_config.on_condition2,
    'condition9': _callback_config.on_condition9,
    'condition8': _callback_config.on_condition8,
    'condition8_pyramid_profit': _callback_config.on_condition8,
}

def should_create_callback_task(condition_type: str, config: CallbackAddConfig = None) -> bool:
    if config is None:
        config = _callback_config
    if not config.enabled:
        return False
    if condition_type in ['board_dynamic_profit', 'board_break', 'board_break_static', 'board_break_dynamic']:
        return False
    return VALID_CALLBACK_CONDITIONS.get(condition_type, False)

def add_callback_task(symbol: str, sell_price: float, prev_close: float,
                      sell_amount: float, sell_quantity: int, condition_type: str,
                      store: AbstractCallbackTaskStore,
                      config: CallbackAddConfig = None) -> Optional[CallbackAdditionTask]:
    if config is None:
        config = _callback_config
    if not should_create_callback_task(condition_type, config):
        return None
    if prev_close <= 0 or sell_price <= 0 or sell_amount <= 0:
        logger.info("【动态回调加仓】%s 参数无效，跳过任务创建", symbol)
        return None

    old_task_data = store.get_task(symbol)
    if old_task_data and old_task_data.get('is_active'):
        old_task = CallbackAdditionTask.from_dict(old_task_data)
        logger.info("【动态回调加仓-任务覆盖】%s 旧任务被强制废止: "
                     "旧基准价=%.4f, 旧回调阈值=%.2f%%, 旧来源=%s",
                     symbol, old_task.sell_price, old_task.callback_threshold * 100, old_task.condition_type)
        logger.info("【动态回调加仓-任务覆盖】%s 新任务覆盖: "
                     "新基准价=%.4f, 新来源=%s", symbol, sell_price, condition_type)

    task = CallbackAdditionTask(
        sell_price=sell_price, prev_close=prev_close,
        sell_amount=sell_amount, sell_quantity=sell_quantity,
        condition_type=condition_type
    )

    if task.buy_quantity < config.min_trade_unit:
        logger.info("【动态回调加仓】%s 折算股数%d低于最小单位%d，任务自动终止。"
                     "卖出金额=%.2f, 触发价=%.4f",
                     symbol, task.buy_quantity, config.min_trade_unit, sell_amount, task.trigger_price)
        task.is_active = False

    store.set_task(symbol, task.to_dict())
    store.save()

    if task.is_active:
        logger.info("【动态回调加仓-任务创建】%s "
                     "基准价=%.4f, 昨日收=%.4f, "
                     "获利幅度R=%.2f%%, "
                     "触发价=%.4f, 计划买入=%d股, 来源=%s",
                     symbol, sell_price, prev_close,
                     task.callback_threshold * 100,
                     task.trigger_price, task.buy_quantity, condition_type)
    return task

def check_callback_strategy(symbol: str, current_price: float,
                            store: AbstractCallbackTaskStore) -> Optional[Dict[str, Any]]:
    if not _callback_config.enabled:
        return None

    task_data = store.get_task(symbol)
    if not task_data:
        return None

    task = CallbackAdditionTask.from_dict(task_data)
    if not task.is_active:
        return None

    if task.is_triggered(current_price):
        logger.info("【动态回调加仓-触发】%s 当前价=%.4f <= 触发价=%.4f, "
                     "获利幅度R=%.2f%%, 计划买入=%d股, 来源=%s",
                     symbol, current_price, task.trigger_price,
                     task.callback_threshold * 100, task.buy_quantity, task.condition_type)
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

def complete_callback_task(symbol: str, store: AbstractCallbackTaskStore) -> None:
    task_data = store.get_task(symbol)
    if task_data:
        task = CallbackAdditionTask.from_dict(task_data)
        task.complete()
        store.set_task(symbol, task.to_dict())
        store.save()
        logger.info("【动态回调加仓-完成】%s 任务已完成并标记失效", symbol)

def remove_callback_task(symbol: str, condition_type: Optional[str] = None,
                         store: AbstractCallbackTaskStore = None) -> bool:
    if store is None:
        return False
    task_data = store.get_task(symbol)
    if not task_data:
        return False
    if condition_type and task_data.get('condition_type') != condition_type:
        return False
    task = CallbackAdditionTask.from_dict(task_data)
    task.is_active = False
    store.set_task(symbol, task.to_dict())
    store.save()
    logger.info("【动态回调加仓-移除】%s 任务已被移除/废止", symbol)
    return True

def get_callback_task(symbol: str, store: AbstractCallbackTaskStore) -> Optional[CallbackAdditionTask]:
    task_data = store.get_task(symbol)
    if task_data:
        task = CallbackAdditionTask.from_dict(task_data)
        if task.is_active:
            return task
    return None

def get_all_active_tasks(store: AbstractCallbackTaskStore) -> Dict[str, CallbackAdditionTask]:
    active_tasks = {}
    for symbol, task_data in store.all_tasks().items():
        if task_data.get('is_active'):
            active_tasks[symbol] = CallbackAdditionTask.from_dict(task_data)
    return active_tasks