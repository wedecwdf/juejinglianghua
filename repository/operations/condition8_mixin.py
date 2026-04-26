# repository/operations/condition8_mixin.py
# -*- coding: utf-8 -*-
"""
条件8特殊状态管理 Mixin：成交记录、撤单回退、撤单锁
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from repository.core.state_gateway_impl import _StateGatewayImpl


class _Condition8Mixin:
    """
    维护条件8的动态基准价、防重复撤单锁、成交瞬间状态
    """

    def acquire_cancel_lock(self: "_StateGatewayImpl", symbol: str) -> bool:
        """尝试获取某股票的撤单锁，成功返回 True"""
        if symbol in self._cancelling_symbols:
            return False
        self._cancelling_symbols.add(symbol)
        return True

    def release_cancel_lock(self: "_StateGatewayImpl", symbol: str) -> None:
        """释放撤单锁"""
        self._cancelling_symbols.discard(symbol)

    def is_cancelling(self: "_StateGatewayImpl", symbol: str) -> bool:
        """查询某股票是否正在撤单中"""
        return symbol in self._cancelling_symbols

    def mark_cancelled(self: "_StateGatewayImpl", symbol: str) -> None:
        """标记某股票已撤单，供 handle_tick 检测后重新判断"""
        self._cancelled_symbols.add(symbol)

    def pop_cancelled(self: "_StateGatewayImpl", symbol: str) -> bool:
        """取出并清除某股票的撤单标记"""
        if symbol in self._cancelled_symbols:
            self._cancelled_symbols.discard(symbol)
            return True
        return False

    def record_condition8_done_price(self: "_StateGatewayImpl", symbol: str, done_price: float) -> None:
        """
        成交瞬间调用，记录真正的成功买入/卖出价，并：
        1. 更新 condition8_reference_price 为真实成交价
        2. 清空挂单价防止误用
        3. 重置当前基准价下的挂单状态标志（允许再次触发）
        """
        if symbol not in self.current_day_data:
            return
        day_data = self.current_day_data[symbol]
        day_data.condition8_last_done_price = done_price
        day_data.condition8_has_done_trade = True
        day_data.condition8_reference_price = done_price
        day_data.condition8_last_trade_price = None
        day_data.condition8_sell_triggered_for_current_ref = False
        day_data.condition8_buy_triggered_for_current_ref = False
        print(f"【成交记录】{symbol} 记录成功成交价:{done_price:.4f}，更新基准价并重置挂单状态")

    def clear_condition8_state(self: "_StateGatewayImpl", symbol: str) -> None:
        """
        撤单完成时回退到最近一次成功成交价（若从未成交则回退到初始基准价）
        """
        if symbol not in self.current_day_data:
            return
        day_data = self.current_day_data[symbol]
        if day_data.condition8_has_done_trade and day_data.condition8_last_done_price is not None:
            day_data.condition8_reference_price = day_data.condition8_last_done_price
            print(f"【撤单回退】{symbol} 回退到最近一次成功成交价:{day_data.condition8_last_done_price:.4f}")
        else:
            day_data.condition8_reference_price = day_data.base_price
            print(f"【撤单回退】{symbol} 回退到初始基准价:{day_data.base_price:.4f}")

        day_data.condition8_last_trade_price = None
        day_data.condition8_sell_triggered_for_current_ref = False
        day_data.condition8_buy_triggered_for_current_ref = False
        print(f"【撤单回退】{symbol} 状态已清空，可再次触发")

    def get_sleep_state(self: "_StateGatewayImpl") -> bool:
        """获取全局休眠状态（用于条件8全局休眠）"""
        return self._sleep_state

    def set_sleep_state(self: "_StateGatewayImpl", state: bool) -> None:
        """设置全局休眠状态"""
        self._sleep_state = state

    def is_condition8_sleeping(self: "_StateGatewayImpl") -> bool:
        """查询当前是否处于条件8休眠模式"""
        return self._sleep_state