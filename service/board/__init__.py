# -*- coding: utf-8 -*-
"""
板数、断板、炸板业务逻辑子模块

拆分版：原 board_service.py 拆分至以下文件：
- counting_service.py      : 板数计数（首板/连板）
- break_service.py         : 断板机制（次日静态止损）
- dynamic_profit_service.py: 炸板动态止盈（状态机驱动）
- state_machine.py         : 状态机基类与工具函数（内部使用）
"""
from __future__ import annotations

from .counting_service import handle_board_counting
from .break_service import handle_board_break_mechanism
from .dynamic_profit_service import handle_dynamic_profit_on_board_break

__all__ = [
    'handle_board_counting',
    'handle_board_break_mechanism',
    'handle_dynamic_profit_on_board_break',
]