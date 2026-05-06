# service/board_service.py
# -*- coding: utf-8 -*-
"""
板数、断板、炸板业务逻辑 - 拆分版代理文件
所有导出的函数签名与子模块一致，配置参数显式传递。
"""

from __future__ import annotations

from service.board import (
    handle_board_counting,
    handle_board_break_mechanism,
    handle_dynamic_profit_on_board_break,
)

__all__ = [
    'handle_board_counting',
    'handle_board_break_mechanism',
    'handle_dynamic_profit_on_board_break',
]