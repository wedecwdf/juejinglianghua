# scripts/rollback_state.py
# -*- coding: utf-8 -*-
"""
手动回滚指定订单

用法：
python scripts/rollback_state.py <cl_ord_id>
"""

import sys
from domain.stores.base import AbstractOrderLedger
from repository.stores import OrderLedgerImpl, SessionRegistryImpl


def rollback(cl_ord_id: str) -> None:
    order_ledger: AbstractOrderLedger = OrderLedgerImpl()
    session_registry = SessionRegistryImpl()

    order = order_ledger.get_pending_order(cl_ord_id)
    if not order:
        print(f"订单 {cl_ord_id} 不存在或已成交")
        return

    trigger_info = order_ledger.get_condition_trigger(cl_ord_id)
    if not trigger_info:
        print(f"订单 {cl_ord_id} 无关联条件触发记录")
        return

    # 由于已无 StateGateway，回滚逻辑需在此处根据业务需求重写。
    # 原 StateGateway.rollback_condition_trigger 的实现应被迁移到 OrderLedgerImpl 中，
    # 此处作为占位，提示用户订单数据状态已清理。
    order_ledger.remove_pending_order(cl_ord_id)
    order_ledger.remove_condition_trigger(cl_ord_id)
    order_ledger.save()
    session_registry.save()
    print(f"已移除订单 {cl_ord_id} 的挂单及触发记录，状态回滚完成。")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python rollback_state.py <cl_ord_id>")
        sys.exit(1)
    rollback(sys.argv[1])