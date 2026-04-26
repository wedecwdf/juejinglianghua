# repository/operations/order_mixin.py
# -*- coding: utf-8 -*-
"""
订单与条件触发管理 Mixin
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from repository.core.state_gateway_impl import _StateGatewayImpl


class _OrderMixin:
    """
    管理 pending_orders, condition_triggers, condition8_pending 池
    """

    def add_pending_order(self: "_StateGatewayImpl", cl_ord_id: str, data: Dict[str, Any]) -> None:
        """添加挂单记录，并自动维护 condition8_pending 双向挂单池"""
        self.pending_orders[cl_ord_id] = data
        self._save_pending_orders()

        symbol = data["symbol"]
        side = data["side"]
        if data.get("condition_type") == "condition8":
            pool = self.condition8_pending.setdefault(symbol, {})
            pool["buy_cl_ord_id" if side == "买入" else "sell_cl_ord_id"] = cl_ord_id

    def remove_pending_order(self: "_StateGatewayImpl", cl_ord_id: str) -> None:
        """移除挂单，并同步清理 condition8_pending 池"""
        data = self.pending_orders.pop(cl_ord_id, None)
        if data and data.get("condition_type") == "condition8":
            symbol = data["symbol"]
            pool = self.condition8_pending.get(symbol, {})
            side = data["side"]
            key = "buy_cl_ord_id" if side == "买入" else "sell_cl_ord_id"
            pool.pop(key, None)
            if not pool:
                self.condition8_pending.pop(symbol, None)
        self._save_pending_orders()

    def get_pending_order(self: "_StateGatewayImpl", cl_ord_id: str) -> Optional[Dict[str, Any]]:
        """获取指定挂单详情"""
        return self.pending_orders.get(cl_ord_id)

    def add_pending_condition_trigger(self: "_StateGatewayImpl", cl_ord_id: str, trigger_info: Dict[str, Any]) -> None:
        """记录某订单关联的条件触发信息，用于成交失败时回滚状态"""
        self.condition_triggers[cl_ord_id] = trigger_info
        self._save_condition_triggers()

    def remove_pending_condition_trigger(self: "_StateGatewayImpl", cl_ord_id: str) -> None:
        """移除条件触发记录"""
        self.condition_triggers.pop(cl_ord_id, None)
        self._save_condition_triggers()

    def get_pending_condition_trigger(self: "_StateGatewayImpl", cl_ord_id: str) -> Optional[Dict[str, Any]]:
        """获取条件触发记录"""
        return self.condition_triggers.get(cl_ord_id)

    def cancel_condition8_opposite(self: "_StateGatewayImpl", symbol: str, keep_cl_ord_id: str) -> None:
        """
        条件8成交后撤销另一方向挂单；带 account_id 兜底与异常隔离
        """
        pool = self.condition8_pending.get(symbol, {}).copy()
        for key, cl_oid in pool.items():
            if cl_oid and cl_oid != keep_cl_ord_id:
                order = self.pending_orders.get(cl_oid)
                if not order:
                    continue

                account_id = order.get("account_id")
                if account_id is None or account_id == "":
                    from config.account import ACCOUNT_ID
                    account_id = ACCOUNT_ID
                    if account_id:
                        order["account_id"] = account_id
                        self.pending_orders[cl_oid] = order
                        print(f"【条件八互斥撤单】{symbol} 订单 {cl_oid} 无 account_id，使用默认账户: {account_id}")
                    else:
                        print(f"【条件八互斥撤单】{symbol} 订单 {cl_oid} 无有效 account_id，跳过撤单")
                        continue

                from repository.gm_data_source import cancel_order
                try:
                    cancel_order(cl_oid, account_id=account_id)
                    print(f"【条件八互斥撤单】{symbol} 撤销对立挂单 {cl_oid}")
                    self.remove_pending_order(cl_oid)
                except Exception as e:
                    print(f"【条件八互斥撤单失败】{symbol} 撤销 {cl_oid} 失败: {e}")