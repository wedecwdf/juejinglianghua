# repository/operations/rollback_mixin.py
# -*- coding: utf-8 -*-
"""
状态回滚 Mixin：成交失败或撤单后回退业务状态

【变更】
1. 条件类型 condition8_pyramid_profit 改为 pyramid_profit
2. 状态字段 condition8_pyramid_profit_status 改为 pyramid_profit_status
3. 移除对 condition8_trade_times 的修改（金字塔已独立，不再计入条件8交易次数）
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from repository.core.state_gateway_impl import _StateGatewayImpl


class _RollbackMixin:
    """
    提供 rollback_condition_trigger 实现
    支持动态回调加仓任务的回滚（替代原金字塔加仓回滚）
    """

    def rollback_condition_trigger(self: "_StateGatewayImpl",
                                   trigger_info: Dict[str, Any]) -> None:
        """
        根据 trigger_info 回退各类条件的触发状态
        包含动态回调加仓任务的回滚逻辑：
        - 如果卖出被回滚，则移除对应的未执行回调加仓任务
        """
        symbol = trigger_info["symbol"]
        condition_type = trigger_info["condition_type"]
        data = trigger_info["trigger_data"]

        if symbol not in self.current_day_data:
            return

        day_data = self.current_day_data[symbol]

        # 动态止盈（条件 2）
        if condition_type == "condition2":
            day_data.dynamic_profit_triggered = data.get("pre_trigger_state", False)
            day_data.dynamic_profit_high_price = data.get("pre_high_price", -float("inf"))
            day_data.dynamic_profit_line = data.get("pre_profit_line", -float("inf"))
            day_data.dynamic_profit_sell_times = max(0, day_data.dynamic_profit_sell_times - 1)
            day_data.total_sell_times = max(0, day_data.total_sell_times - 1)
            day_data.condition2_triggered_and_sold = False
            # 回滚对应的动态回调加仓任务（如果存在且未执行）
            from service.pyramid_service import remove_callback_task
            remove_callback_task(symbol, 'condition2')
            print(f"【回退状态】{symbol} 条件2触发状态已回退，关联的动态回调加仓任务已移除")

        # 条件 4/5/6/7 保持原逻辑...
        elif condition_type == "condition4":
            day_data.buy_condition4_triggered = False
            qty = data.get("quantity", 0)
            self.total_buy_quantity[symbol] = max(0, self.total_buy_quantity.get(symbol, 0) - qty)
            print(f"【回退状态】{symbol} 条件4触发状态已回退")

        elif condition_type == "condition5":
            day_data.buy_condition5_triggered = False
            qty = data.get("quantity", 0)
            self.total_buy_quantity[symbol] = max(0, self.total_buy_quantity.get(symbol, 0) - qty)
            print(f"【回退状态】{symbol} 条件5触发状态已回退")

        elif condition_type == "condition6":
            day_data.buy_condition6_triggered = False
            qty = data.get("quantity", 0)
            self.total_buy_quantity[symbol] = max(0, self.total_buy_quantity.get(symbol, 0) - qty)
            print(f"【回退状态】{symbol} 条件6触发状态已回退")

        elif condition_type == "condition7":
            day_data.condition7_triggered = False
            pre_qty = data.get("pre_buy_quantity", self.total_buy_quantity.get(symbol, 0))
            self.total_buy_quantity[symbol] = pre_qty
            print(f"【回退状态】{symbol} 条件7触发状态已回退")

        # 条件 8 动态基准价交易
        elif condition_type == "condition8":
            day_data.condition8_trade_times = max(0, day_data.condition8_trade_times - 1)
            day_data.condition8_reference_price = data.get("pre_ref_price", day_data.condition8_reference_price)
            day_data.condition8_last_trade_price = data.get("pre_trade_price", day_data.condition8_last_trade_price)
            current_ref = data.get("current_ref_price")
            if current_ref is not None and math.isclose(current_ref, day_data.condition8_reference_price, rel_tol=1e-5):
                side = data.get("side")
                if side == "sell":
                    day_data.condition8_sell_triggered_for_current_ref = False
                elif side == "buy":
                    day_data.condition8_buy_triggered_for_current_ref = False
            print(f"【回退状态】{symbol} 条件8触发状态已回退，挂单状态已重置")

        # 条件 9
        elif condition_type == "condition9":
            day_data.condition9_triggered = data.get("pre_trigger_state", False)
            day_data.condition9_high_price = data.get("pre_high_price", -float('inf'))
            day_data.condition9_profit_line = data.get("pre_profit_line", -float('inf'))
            day_data.condition9_sell_times = max(0, day_data.condition9_sell_times - 1)
            day_data.total_sell_times = max(0, day_data.total_sell_times - 1)
            day_data.condition9_triggered_for_spacing = False
            # 回滚对应的动态回调加仓任务
            from service.pyramid_service import remove_callback_task
            remove_callback_task(symbol, 'condition9')
            print(f"【回退状态】{symbol} 条件9触发状态已回退，关联的动态回调加仓任务已移除")

        # 【变更】金字塔止盈（完全独立机制）
        elif condition_type == "pyramid_profit":
            pyramid_level = data.get("pyramid_level", -1)
            pyramid_status = data.get("pyramid_status", [False, False, False])
            if 0 <= pyramid_level < 3:
                # 【变更】使用独立的状态字段 pyramid_profit_status
                day_data.pyramid_profit_status = pyramid_status
                day_data.pyramid_profit_triggered = any(pyramid_status)  # 根据状态重新计算触发标记
                # 【变更】不再修改 condition8_trade_times（已独立）
                day_data.total_sell_times = max(0, day_data.total_sell_times - 1)
                # 回滚对应的动态回调加仓任务（金字塔卖出产生的）
                from service.pyramid_service import remove_callback_task
                remove_callback_task(symbol, 'pyramid_profit')
                print(
                    f"【回退状态】{symbol} 金字塔止盈第{pyramid_level + 1}级状态已回退（独立机制），关联的动态回调加仓任务已移除")

        # 动态回调加仓任务本身的回滚（如果加仓买入失败需要回滚）
        elif condition_type == "callback_addition":
            # 恢复任务状态为激活（如果之前被标记为完成）
            task_data = self.callback_addition_tasks.get(symbol)
            if task_data:
                task_data['is_active'] = True
                self.callback_addition_tasks[symbol] = task_data
            print(f"【回退状态】{symbol} 动态回调加仓任务状态已恢复")

        # 次日调整机制
        elif condition_type == "dynamic_profit_next_day_adjustment":
            day_data.dynamic_profit_next_day_adjustment = data.get("pre_adjustment_data", {})
            print(f"【回退状态】{symbol} 动态止盈次日调整机制状态已回退")

        self.save_all()