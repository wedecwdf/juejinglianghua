# domain/conditions/board_mechanisms.py
# -*- coding: utf-8 -*-
"""
占位条件：板机制综合处理（当前未启用）。
已完全解耦 service 层，若将来需要实现，应通过依赖注入传入具体函数。
"""

from domain.decisions import Condition


class BoardMechanismsCondition(Condition):
    condition_name = 'board_mechanisms'
    is_side_effect = False
    depends_on = []

    def evaluate(self, symbol, current_price, available_position, day_data, base_price, ctx, shared_state):
        # 暂无实现
        return None