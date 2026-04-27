# domain/conditions/board.py
# -*- coding: utf-8 -*-
"""板数/炸板/断板机制包装，暂不改变内部执行，仅封装为 Condition 接口"""
from __future__ import annotations
from typing import Optional
from domain.decisions import Condition, Decision
from service.execution.board_executor import execute_board_mechanisms


class BoardMechanismsCondition(Condition):
    def evaluate(self, symbol: str, current_price: float, available_position: int,
                 day_data, base_price: float, ctx) -> Optional[Decision]:
        """
        直接调用原执行器，内部已处理下单和状态更新。
        返回 None 表示已自行处理，无需仲裁器再决策。
        """
        executed = execute_board_mechanisms(
            symbol, current_price, ctx.tick_time, available_position,
            day_data, base_price, ctx.board_repo, ctx.session_registry
        )
        return None  # 执行器已自行处理，仲裁器无需再动作