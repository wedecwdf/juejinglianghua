# service/order_cancel_service.py
# -*- coding: utf-8 -*-
"""
自动撤单服务：定时扫描未成交委托，超时即撤。
添加锁保护全局集合。
"""
from __future__ import annotations
import threading
import time
from datetime import datetime
from typing import List, Dict, Any
from gm.api import get_unfinished_orders, order_cancel as gm_order_cancel
from config.strategy import (
    AUTO_CANCEL_ENABLED,
    AUTO_CANCEL_TIMEOUT,
    AUTO_CANCEL_CHECK_INTERVAL,
    CONDITION8_CANCEL_TIMEOUT,
)
from config.account import ACCOUNT_ID
from repository.mail_sender import send_email
from domain.stores import OrderLedger, SessionRegistry

_canceling_now: set[str] = set()
_canceling_lock = threading.Lock()

def _cancel_timeout_orders(order_ledger: OrderLedger, session_registry: SessionRegistry) -> None:
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

            local_order = order_ledger.get_pending_order(cl_ord_id)
            is_condition8 = bool(local_order and local_order.get('condition_type') == 'condition8')
            condition_type = local_order.get('condition_type') if local_order else None
            is_condition2 = (condition_type == 'condition2')
            is_condition9 = (condition_type == 'condition9')

            timeout = CONDITION8_CANCEL_TIMEOUT if is_condition8 else AUTO_CANCEL_TIMEOUT
            if now_ts - created_ts > timeout:
                account_id = (local_order.get('account_id') if local_order else None) or o.get('account_id') or ACCOUNT_ID
                if account_id is None or account_id == "":
                    print(f'【撤单跳过】{o["symbol"]} 订单 {cl_ord_id} 无有效 account_id')
                    continue
                if local_order and 'account_id' not in local_order:
                    order_ledger.add_pending_order(cl_ord_id, {**local_order, 'account_id': account_id})

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
                print(f'【超时识别】{o["symbol"]} 订单 {cl_ord_id} '
                      f'{"条件8" if is_condition8 else ("条件2" if is_condition2 else ("条件9" if is_condition9 else "普通"))}订单超时: '
                      f'创建时间{datetime.fromtimestamp(created_ts).strftime("%H:%M:%S")}, 超时{timeout}秒')

        if not to_cancel:
            return

        for item in to_cancel:
            symbol = item["symbol"]
            if order_ledger.acquire_cancel_lock(symbol):
                print(f'【撤单保护】{symbol} 获得撤单锁，开始撤单')
            else:
                print(f'【撤单保护】{symbol} 已在撤单中，跳过本次撤单')
                item["cl_ord_id"] = None

        to_cancel = [i for i in to_cancel if i["cl_ord_id"] is not None]
        if not to_cancel:
            for item in to_cancel:
                order_ledger.release_cancel_lock(item["symbol"])
            return

        final_cancel = [{"cl_ord_id": i["cl_ord_id"], "account_id": i["account_id"]} for i in to_cancel]
        if final_cancel:
            gm_order_cancel(wait_cancel_orders=final_cancel)
            condition8_count = sum(1 for i in to_cancel if i.get("is_condition8"))
            condition2_count = sum(1 for i in to_cancel if i.get("is_condition2"))
            condition9_count = sum(1 for i in to_cancel if i.get("is_condition9"))
            normal_count = len(to_cancel) - condition8_count - condition2_count - condition9_count
            print(f'【自动撤单】已撤销 {len(final_cancel)} 笔超时委托 (条件8: {condition8_count}笔, 条件2: {condition2_count}笔, 条件9: {condition9_count}笔, 普通: {normal_count}笔)')

            for item in to_cancel:
                cl_ord_id = item["cl_ord_id"]
                symbol = item["symbol"]
                order_ledger.remove_pending_order(cl_ord_id)

                if item.get("is_condition8"):
                    order_ledger.clear_condition8_state(symbol)
                    print(f'【条件8撤单清理】{symbol} 状态重置完成')

                if item.get("is_condition2") or item.get("is_condition9"):
                    day_data = session_registry.get(symbol)
                    if day_data:
                        if item.get("is_condition2"):
                            day_data.condition2_recheck_after_cancel = True
                            print(f'【条件2撤单标记】{symbol} 设置重新判定标记')
                        if item.get("is_condition9"):
                            day_data.condition9_recheck_after_cancel = True
                            print(f'【条件9撤单标记】{symbol} 设置重新判定标记')

                order_ledger.mark_cancelled(symbol)
                order_ledger.release_cancel_lock(symbol)
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
        print(f'自动撤单异常: {e}')
        send_email("自动撤单异常", str(e))

def _loop(order_ledger: OrderLedger, session_registry: SessionRegistry) -> None:
    while True:
        if AUTO_CANCEL_ENABLED:
            _cancel_timeout_orders(order_ledger, session_registry)
        time.sleep(AUTO_CANCEL_CHECK_INTERVAL)

def start_auto_cancel_thread(order_ledger: OrderLedger, session_registry: SessionRegistry) -> None:
    if not AUTO_CANCEL_ENABLED:
        return
    t = threading.Thread(target=_loop, args=(order_ledger, session_registry), daemon=True)
    t.start()
    print(f'【自动撤单服务】启动成功，条件8订单超时{CONDITION8_CANCEL_TIMEOUT}秒，普通订单超时{AUTO_CANCEL_TIMEOUT}秒')