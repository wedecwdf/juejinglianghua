# scripts/rollback_state.py
# -*- coding: utf-8 -*-
"""
手动回滚指定订单
用法：
python scripts/rollback_state.py <cl_ord_id>
"""
import sys
from domain.stores import OrderLedger, SessionRegistry

def rollback(cl_ord_id: str) -> None:
    order_ledger = OrderLedger()
    session_registry = SessionRegistry()

    order = order_ledger.get_pending_order(cl_ord_id)
    if not order:
        print(f"订单 {cl_ord_id} 不存在或已成交")
        return

    trigger_info = order_ledger.get_condition_trigger(cl_ord_id)
    if not trigger_info:
        print(f"订单 {cl_ord_id} 无关联条件触发记录")
        return

    # 通过底层 StateGateway 进行状态回滚（脚本临时引用，不影响核心架构）
    from repository.state_gateway import StateGateway
    gw = StateGateway()
    gw.rollback_condition_trigger(trigger_info)

    order_ledger.remove_pending_order(cl_ord_id)
    order_ledger.remove_condition_trigger(cl_ord_id)

    order_ledger.save()
    session_registry.save()

    print(f"已回滚订单 {cl_ord_id}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python rollback_state.py <cl_ord_id>")
        sys.exit(1)
    rollback(sys.argv[1])