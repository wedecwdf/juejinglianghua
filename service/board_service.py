# -*- coding: utf-8 -*-
"""
板数、断板、炸板业务逻辑 - 拆分版代理文件

原文件逻辑已拆分至 board/ 子目录：
- board/counting_service.py      : 板数计数
- board/break_service.py         : 断板机制
- board/dynamic_profit_service.py: 炸板动态止盈
- board/state_machine.py         : 状态机核心（内部使用）

本文件仅做重新导出以保持对外接口 100% 兼容，
旧代码中 `from service.board_service import handle_board_counting` 继续有效。
"""
from __future__ import annotations

# 从子模块重新导出所有公共函数（保持与原文件完全一致的导出列表）
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