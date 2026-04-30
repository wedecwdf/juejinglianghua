# service/order_cancel_service.py
# -*- coding: utf-8 -*-
"""
自动撤单服务，撤单参数从环境变量读取，不再依赖 config.strategy。
"""
from __future__ import annotations
import logging
import os
import threading
import time
from datetime import datetime
from typing import List, Dict, Any
from gm.api import get_unfinished_orders, order_cancel as gm_order_cancel
from config.account import ACCOUNT_ID
from repository.mail_sender import send_email
from domain.stores.order_interfaces import OrderRepository, CancelLockManager
from domain.stores.base import AbstractSessionRegistry
from domain.stores.context_store import ContextStore

logger = logging.getLogger(__name__)

# 撤单参数直接从环境变量读取
AUTO_CANCEL_ENABLED: bool = os.getenv('AUTO_CANCEL_ENABLED', 'true').lower() == 'true'
AUTO_CANCEL_TIMEOUT: int = int(os.getenv('AUTO_CANCEL_TIMEOUT', '5'))
AUTO_CANCEL_CHECK_INTERVAL: int = int(os.getenv('AUTO_CANCEL_CHECK_INTERVAL', '5'))
CONDITION8_CANCEL_TIMEOUT: int = int(os.getenv('CONDITION8_CANCEL_TIMEOUT', '6000'))

_canceling_now: set[str] = set()
_canceling_lock = threading.Lock()


def _cancel_timeout_orders(order_repo: OrderRepository,
                           cancel_lock_manager: CancelLockManager,
                           session_registry: AbstractSessionRegistry,
                           context_store: ContextStore) -> None:
    try:
        unf = get_unfinished_orders()
        if not unf:
            return

        now_ts = datetime.now().timestamp()
        to_cancel: List[Dict[str, Any]] = []

        for o in unf:
            cl_ord_id = o.get('cl_ord_id')
            with _canceling_lock:
                if not cl_ord_id or cl_ord_id in _canceling_now:
                    continue
            created = o.get('created_at')
            if created is None:
                continue
            if isinstance(created, datetime):
                created_ts = created.timestamp()
            else:
                try:
                    created_ts = datetime.fromisoformat(str(created)).timestamp()
                except Exception:
                    continue

            local_order = order_repo.get_pending_order(cl_ord_id)
            is_condition8 = bool(local_order and local_order.get('condition_type') == 'condition8')
            condition_type = local_order.get('condition_type') if local_order else None
            is_condition2 = (condition_type == 'condition2')
            is_condition9 = (condition_type == 'condition9')

            timeout = CONDITION8_CANCEL_TIMEOUT if is_condition8 else AUTO_CANCEL_TIMEOUT
            if now_ts - created_ts > timeout:
                account_id = (local_order.get('account_id') if local_order else None) or o.get('account_id') or ACCOUNT_ID
                if account_id is None or account_id == "":
                    logger.info('【撤单跳过】%s 订单 %s 无有效 account_id', o["symbol"], cl_ord_id)
                    continue
                if local_order and 'account_id' not in local_order:
                    order_repo.add_pending_order(cl_ord_id, {**local_order, 'account_id': account_id})

                to_cancel.append({
                    "cl_ord_id": cl_ord_id,
                    "account_id": account_id,
                    "symbol": o["symbol"],
                    "is_condition8": is_condition8,
                    "condition_type": condition_type,
                    "is_condition2": is_condition2,
                    "is_condition9": is_condition9,
                })
                with _canceling_lock:
                    _canceling_now.add(cl_ord_id)
                logger.info(
                    '【超时识别】%s 订单 %s %s订单超时: 创建时间%s, 超时%d秒',
                    o["symbol"], cl_ord_id,
                    "条件8" if is_condition8 else ("条件2" if is_condition2 else ("条件9" if is_condition9 else "普通")),
                    datetime.fromtimestamp(created_ts).strftime("%H:%M:%S"), timeout
                )

        if not to_cancel:
            return

        for item in to_cancel:
            symbol = item["symbol"]
            if cancel_lock_manager.acquire_cancel_lock(symbol):
                logger.info('【撤单保护】%s 获得撤单锁，开始撤单', symbol)
            else:
                logger.info('【撤单保护】%s 已在撤单中，跳过本次撤单', symbol)
                item["cl_ord_id"] = None

        to_cancel = [i for i in to_cancel if i["cl_ord_id"] is not None]
        if not to_cancel:
            for item in to_cancel:
                cancel_lock_manager.release_cancel_lock(item["symbol"])
            return

        final_cancel = [{"cl_ord_id": i["cl_ord_id"], "account_id": i["account_id"]} for i in to_cancel]
        if final_cancel:
            gm_order_cancel(wait_cancel_orders=final_cancel)
            condition8_count = sum(1 for i in to_cancel if i.get("is_condition8"))
            condition2_count = sum(1 for i in to_cancel if i.get("is_condition2"))
            condition9_count = sum(1 for i in to_cancel if i.get("is_condition9"))
            normal_count = len(to_cancel) - condition8_count - condition2_count - condition9_count
            logger.info(
                '【自动撤单】已撤销 %d 笔超时委托 (条件8: %d笔, 条件2: %d笔, 条件9: %d笔, 普通: %d笔)',
                len(final_cancel), condition8_count, condition2_count, condition9_count, normal_count
            )

            for item in to_cancel:
                cl_ord_id = item["cl_ord_id"]
                symbol = item["symbol"]
                order_repo.remove_pending_order(cl_ord_id)

                if item.get("is_condition2") or item.get("is_condition9"):
                    try:
                        ctx2 = context_store.get('condition2', symbol)
                        if item.get("is_condition2"):
                            ctx2.recheck_after_cancel = True
                            logger.info('【条件2撤单标记】%s 设置重新判定标记', symbol)
                    except KeyError:
                        pass
                    try:
                        ctx9 = context_store.get('condition9', symbol)
                        if item.get("is_condition9"):
                            ctx9.recheck_after_cancel = True
                            logger.info('【条件9撤单标记】%s 设置重新判定标记', symbol)
                    except KeyError:
                        pass

                cancel_lock_manager.mark_cancelled(symbol)
                cancel_lock_manager.release_cancel_lock(symbol)
                with _canceling_lock:
                    _canceling_now.discard(cl_ord_id)

            send_email("自动撤单触发",
                       f'已撤销 {len(final_cancel)} 笔超时委托\n'
                       f'条件8订单: {condition8_count}笔\n'
                       f'条件2订单: {condition2_count}笔\n'
                       f'条件9订单: {condition9_count}笔\n'
                       f'普通订单: {normal_count}笔\n'
                       f'标的: {",".join({i["symbol"] for i in to_cancel})}')
    except Exception as e:
        logger.exception('自动撤单异常')
        send_email("自动撤单异常", str(e))


def _loop(order_repo: OrderRepository,
          cancel_lock_manager: CancelLockManager,
          session_registry: AbstractSessionRegistry,
          context_store: ContextStore) -> None:
    while True:
        if AUTO_CANCEL_ENABLED:
            _cancel_timeout_orders(order_repo, cancel_lock_manager, session_registry, context_store)
        time.sleep(AUTO_CANCEL_CHECK_INTERVAL)


def start_auto_cancel_thread(order_ledger, session_registry, context_store):
    if not AUTO_CANCEL_ENABLED:
        return
    t = threading.Thread(target=_loop, args=(
        order_ledger.as_order_repo(),
        order_ledger.as_cancel_lock_manager(),
        session_registry,
        context_store,
    ), daemon=True)
    t.start()
    logger.info('【自动撤单服务】启动成功，条件8订单超时%d秒，普通订单超时%d秒',
                CONDITION8_CANCEL_TIMEOUT, AUTO_CANCEL_TIMEOUT)