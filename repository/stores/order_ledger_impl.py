# repository/stores/order_ledger_impl.py
# -*- coding: utf-8 -*-
"""
OrderLedger 实现，同时实现所有拆分后的小接口，并提供拆解方法。
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from domain.stores.order_interfaces import (
    OrderRepository,
    ConditionTriggerRepo,
    CancelLockManager,
    SleepStateManager,
    Condition8OrderTracker,
)
from repository.persistence.file_persistence import FilePersistence
from repository.core.file_path import PENDING_ORDERS_FILE, CONDITION_TRIGGERS_FILE

class OrderLedgerImpl(OrderRepository, ConditionTriggerRepo,
                      CancelLockManager, SleepStateManager,
                      Condition8OrderTracker):
    def __init__(self):
        self._pending_orders: Dict[str, Dict[str, Any]] = {}
        self._condition_triggers: Dict[str, Dict[str, Any]] = {}
        self._condition8_pending: Dict[str, Dict[str, str]] = {}
        self._cancelling_symbols: set[str] = set()
        self._cancelled_symbols: set[str] = set()
        self._sleep_state: bool = False
        self._persistence = FilePersistence()

    # 所有方法实现完全保留（挂单、触发记录、条件8互斥撤单、锁管理、休眠状态），此处省略重复，但必须存在
    # 为了文件完整性，下面是所有方法（与之前相同，但类继承改为平铺的五个接口）

    # ---------- 持久化 ----------
    def load(self) -> None:
        loaded = self._persistence.load(PENDING_ORDERS_FILE)
        if isinstance(loaded, dict):
            self._pending_orders = loaded
        triggers = self._persistence.load(CONDITION_TRIGGERS_FILE)
        if isinstance(triggers, dict):
            self._condition_triggers = triggers

    def save(self) -> None:
        self._persistence.save(PENDING_ORDERS_FILE, self._pending_orders)
        self._persistence.save(CONDITION_TRIGGERS_FILE, self._condition_triggers)

    # ---------- OrderRepository ----------
    def add_pending_order(self, cl_ord_id: str, data: Dict[str, Any]) -> None:
        self._pending_orders[cl_ord_id] = data
        symbol = data["symbol"]
        side = data["side"]
        if data.get("condition_type") == "condition8":
            pool = self._condition8_pending.setdefault(symbol, {})
            pool["buy_cl_ord_id" if side == "买入" else "sell_cl_ord_id"] = cl_ord_id

    def remove_pending_order(self, cl_ord_id: str) -> None:
        data = self._pending_orders.pop(cl_ord_id, None)
        if data and data.get("condition_type") == "condition8":
            symbol = data["symbol"]
            pool = self._condition8_pending.get(symbol, {})
            side = data["side"]
            key = "buy_cl_ord_id" if side == "买入" else "sell_cl_ord_id"
            pool.pop(key, None)
            if not pool:
                self._condition8_pending.pop(symbol, None)

    def get_pending_order(self, cl_ord_id: str) -> Optional[Dict[str, Any]]:
        return self._pending_orders.get(cl_ord_id)

    def get_all_pending_orders(self) -> Dict[str, Dict[str, Any]]:
        return self._pending_orders

    # ---------- ConditionTriggerRepo ----------
    def add_condition_trigger(self, cl_ord_id: str, trigger_info: Dict[str, Any]) -> None:
        self._condition_triggers[cl_ord_id] = trigger_info

    def remove_condition_trigger(self, cl_ord_id: str) -> None:
        self._condition_triggers.pop(cl_ord_id, None)

    def get_condition_trigger(self, cl_ord_id: str) -> Optional[Dict[str, Any]]:
        return self._condition_triggers.get(cl_ord_id)

    # ---------- CancelLockManager ----------
    def acquire_cancel_lock(self, symbol: str) -> bool:
        if symbol in self._cancelling_symbols:
            return False
        self._cancelling_symbols.add(symbol)
        return True

    def release_cancel_lock(self, symbol: str) -> None:
        self._cancelling_symbols.discard(symbol)

    def mark_cancelled(self, symbol: str) -> None:
        self._cancelled_symbols.add(symbol)

    def pop_cancelled(self, symbol: str) -> bool:
        if symbol in self._cancelled_symbols:
            self._cancelled_symbols.discard(symbol)
            return True
        return False

    def is_cancelling(self, symbol: str) -> bool:
        return symbol in self._cancelling_symbols

    # ---------- SleepStateManager ----------
    def get_sleep_state(self) -> bool:
        return self._sleep_state

    def set_sleep_state(self, state: bool) -> None:
        self._sleep_state = state

    def is_condition8_sleeping(self) -> bool:
        return self._sleep_state

    # ---------- Condition8OrderTracker ----------
    def cancel_condition8_opposite(self, symbol: str, keep_cl_ord_id: str) -> None:
        from adapter.gm_adapter import cancel_order
        pool = self._condition8_pending.get(symbol, {}).copy()
        for key, cl_oid in pool.items():
            if cl_oid and cl_oid != keep_cl_ord_id:
                order = self._pending_orders.get(cl_oid)
                if not order:
                    continue
                account_id = order.get("account_id")
                if not account_id:
                    from config.account import ACCOUNT_ID
                    account_id = ACCOUNT_ID
                    order["account_id"] = account_id
                    self._pending_orders[cl_oid] = order
                try:
                    cancel_order(cl_oid, account_id=account_id)
                    print(f"【条件八互斥撤单】{symbol} 撤销对立挂单 {cl_oid}")
                    self.remove_pending_order(cl_oid)
                except Exception as e:
                    print(f"【条件八互斥撤单失败】{symbol} 撤销 {cl_oid} 失败: {e}")

    def get_condition8_pending_pool(self, symbol: str) -> Dict[str, str]:
        return self._condition8_pending.get(symbol, {})

    def record_condition8_done_price(self, symbol: str, done_price: float) -> None:
        # 空实现，待后续迁移到 Condition8OrderTracker 的真实现
        pass

    def clear_condition8_state(self, symbol: str) -> None:
        pass

    # 提供拆解方法，用于构建TickContext时获取各个接口
    def as_order_repo(self) -> OrderRepository:
        return self

    def as_condition_trigger_repo(self) -> ConditionTriggerRepo:
        return self

    def as_cancel_lock_manager(self) -> CancelLockManager:
        return self

    def as_sleep_state_manager(self) -> SleepStateManager:
        return self

    def as_condition8_tracker(self) -> Condition8OrderTracker:
        return self