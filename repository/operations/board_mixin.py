# repository/operations/board_mixin.py
# -*- coding: utf-8 -*-
"""
板数、断板、炸板状态管理 Mixin
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from domain.board import BoardStatus, BoardBreakStatus, BoardCountData

if TYPE_CHECKING:
    from repository.core.state_gateway_impl import _StateGatewayImpl


class _BoardMixin:
    """
    提供 BoardStatus, BoardBreakStatus, BoardCountData 的获取与设置
    """

    def get_board_status(self: "_StateGatewayImpl", symbol: str) -> BoardStatus:
        """获取或创建某股票的炸板/封板状态"""
        return self.board_status.setdefault(symbol, BoardStatus())

    def get_board_count_data(self: "_StateGatewayImpl", symbol: str) -> Optional[BoardCountData]:
        """获取板数计数数据"""
        return self.board_count_data.get(symbol)

    def set_board_count_data(self: "_StateGatewayImpl", symbol: str, data: Optional[BoardCountData]) -> None:
        """设置板数计数数据并立即持久化"""
        if data is None:
            self.board_count_data.pop(symbol, None)
        else:
            self.board_count_data[symbol] = data
        self._save_board_count()

    def get_board_break_status(self: "_StateGatewayImpl", symbol: str) -> BoardBreakStatus:
        """获取或创建断板(静态止损)状态"""
        return self.board_break_status.setdefault(symbol, BoardBreakStatus())