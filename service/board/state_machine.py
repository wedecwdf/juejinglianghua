# -*- coding: utf-8 -*-
"""
炸板动态止盈状态机与板数工具函数

【状态机形式化梳理】
1. 移除 RESEALED 伪状态，重新封板直接由外部逻辑回到 SEALED
2. 状态处理器仅保留 4 个：SEALED / STAGE1_MONITORING / STAGE2_TAKEOVER / TRIGGERED
3. can_transition_to 保持声明式接口（运行时未调用，保留以维持形式化语义）
"""
from __future__ import annotations
from datetime import datetime, time as dt_time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from domain.board import BoardStatus, BoardBreakState
from config.strategy import (
    DYNAMIC_PROFIT_SEALED_SELL_PERCENT,
    DYNAMIC_PROFIT_BREAK_LINE_SELL_PERCENT,
    DYNAMIC_PROFIT_NO_ACTION_SELL_PERCENT,
    BOARD_BREAK_NO_ACTION_SELL_TIME,
    MAIN_BOARD_LIMIT_UP_PERCENT,
    GEM_BOARD_LIMIT_UP_PERCENT,
    ST_BOARD_LIMIT_UP_PERCENT,
    BSE_BOARD_LIMIT_UP_PERCENT,
    LIMIT_UP_TOLERANCE_PERCENT
)

# ------------------ 状态机上下文 ------------------
class BoardBreakContext:
    """
    状态机上下文
    封装状态转换所需的所有数据
    """
    def __init__(self, symbol: str, board_status: BoardStatus,
                 current_price: float, tick_time: datetime,
                 available_position: int):
        self.symbol = symbol
        self.board_status = board_status
        self.current_price = current_price
        self.tick_time = tick_time
        self.available_position = available_position
        self.sell_qty: Optional[int] = None  # 执行结果

# ------------------ 状态基类 ------------------
class BoardBreakStateHandler(ABC):
    """
    炸板动态止盈状态基类
    每个子类对应一个具体状态的处理逻辑
    """
    def __init__(self, context: BoardBreakContext):
        self.ctx = context

    @abstractmethod
    def handle(self) -> Optional[int]:
        """处理当前状态下的逻辑，返回卖出数量或None"""
        pass

    @abstractmethod
    def can_transition_to(self, new_state: BoardBreakState) -> bool:
        """检查是否允许转换到目标状态"""
        pass

# ------------------ 具体状态实现 ------------------
class SealedState(BoardBreakStateHandler):
    """封板中状态"""
    def handle(self) -> Optional[int]:
        # 封板状态不执行动态止盈逻辑
        return None

    def can_transition_to(self, new_state: BoardBreakState) -> bool:
        # 封板可以转换到：阶段①（开板）、已触发（连板时重置）
        return new_state in [BoardBreakState.STAGE1_MONITORING,
                             BoardBreakState.TRIGGERED]

class Stage1MonitoringState(BoardBreakStateHandler):
    """阶段①：开板立即触发机制 - 有限职责"""
    def handle(self) -> Optional[int]:
        """
        阶段①唯一职责：监控股价是否跌破动态止盈线
        不负责：时间判断、重新封板判断、其他卖出场景
        """
        bs = self.ctx.board_status
        # 仅监控跌破止盈线
        if self.ctx.current_price <= bs.board_break_dynamic_profit_line:
            sell_qty = int(self.ctx.available_position *
                           DYNAMIC_PROFIT_BREAK_LINE_SELL_PERCENT)
            sell_qty = (sell_qty // 100) * 100
            if sell_qty > 0:
                # 触发成功，转换到TRIGGERED状态（一次性原则）
                bs.set_break_state(BoardBreakState.TRIGGERED)
                print(f"【状态机：STAGE1->TRIGGERED】{self.ctx.symbol} "
                      f"阶段①触发跌破止盈线卖出，"
                      f"基准价:{bs.last_effective_limit_up_price:.4f}，卖出{sell_qty}股")
                return sell_qty
        return None

    def can_transition_to(self, new_state: BoardBreakState) -> bool:
        # 阶段①可以转换到：TRIGGERED（触发）、STAGE2（超时接管）
        return new_state in [BoardBreakState.TRIGGERED,
                             BoardBreakState.STAGE2_TAKEOVER]

class Stage2TakeoverState(BoardBreakStateHandler):
    """阶段②：炸板确认接管机制 - 完整职责"""
    def handle(self) -> Optional[int]:
        """
        阶段②完整职责：
        1. 再次封板动态止盈卖出
        2. 跌破止盈线动态止盈卖出（接管阶段①未完成的职责）
        3. 尾盘无动作动态止盈卖出
        """
        bs = self.ctx.board_status
        current_time = self.ctx.tick_time.time()
        no_action_time = _parse_time_string(BOARD_BREAK_NO_ACTION_SELL_TIME)

        # 职责一：再次封板动态止盈卖出
        if bs.is_sealed and bs.effective_sealed:
            sell_qty = int(self.ctx.available_position *
                           DYNAMIC_PROFIT_SEALED_SELL_PERCENT)
            sell_qty = (sell_qty // 100) * 100
            if sell_qty > 0:
                bs.set_break_state(BoardBreakState.TRIGGERED)
                print(f"【状态机：STAGE2->TRIGGERED】{self.ctx.symbol} "
                      f"阶段②-再次封板卖出，"
                      f"基准价:{bs.last_effective_limit_up_price:.4f}，卖出{sell_qty}股")
                return sell_qty

        # 职责二：跌破止盈线动态止盈卖出（接管阶段①未触发的职责）
        if self.ctx.current_price <= bs.board_break_dynamic_profit_line:
            sell_qty = int(self.ctx.available_position *
                           DYNAMIC_PROFIT_BREAK_LINE_SELL_PERCENT)
            sell_qty = (sell_qty // 100) * 100
            if sell_qty > 0:
                bs.set_break_state(BoardBreakState.TRIGGERED)
                print(f"【状态机：STAGE2->TRIGGERED】{self.ctx.symbol} "
                      f"阶段②-跌破止盈线卖出（接管），"
                      f"基准价:{bs.last_effective_limit_up_price:.4f}，卖出{sell_qty}股")
                return sell_qty

        # 职责三：尾盘无动作动态止盈卖出
        if current_time >= no_action_time:
            sell_qty = int(self.ctx.available_position *
                           DYNAMIC_PROFIT_NO_ACTION_SELL_PERCENT)
            sell_qty = (sell_qty // 100) * 100
            if sell_qty > 0:
                bs.set_break_state(BoardBreakState.TRIGGERED)
                print(f"【状态机：STAGE2->TRIGGERED】{self.ctx.symbol} "
                      f"阶段②-尾盘无动作卖出，"
                      f"基准价:{bs.last_effective_limit_up_price:.4f}，卖出{sell_qty}股")
                return sell_qty
        return None

    def can_transition_to(self, new_state: BoardBreakState) -> bool:
        # 阶段②可以转换到：TRIGGERED（触发）
        return new_state in [BoardBreakState.TRIGGERED]

class TriggeredState(BoardBreakStateHandler):
    """已触发状态（一次性原则：当日不再重新激活）"""
    def handle(self) -> Optional[int]:
        # 已触发状态不再执行任何操作（当日结束）
        return None

    def can_transition_to(self, new_state: BoardBreakState) -> bool:
        # 已触发只能在新交易日通过连板重置到SEALED（外部处理）
        return False

# ------------------ 状态工厂 ------------------
class BoardBreakStateFactory:
    """状态工厂：根据当前状态创建对应的状态处理器"""
    @staticmethod
    def create_state(state: BoardBreakState,
                     context: BoardBreakContext) -> BoardBreakStateHandler:
        state_map = {
            BoardBreakState.SEALED: SealedState,
            BoardBreakState.STAGE1_MONITORING: Stage1MonitoringState,
            BoardBreakState.STAGE2_TAKEOVER: Stage2TakeoverState,
            BoardBreakState.TRIGGERED: TriggeredState
        }
        handler_class = state_map.get(state)
        if handler_class:
            return handler_class(context)
        raise ValueError(f"未知状态: {state}")

# ------------------ 工具函数（原 board_service 工具层） ------------------
def _parse_time_string(time_str: str) -> dt_time:
    """解析时间字符串"""
    try:
        hour, minute = map(int, time_str.split(':'))
        return dt_time(hour, minute)
    except Exception:
        return dt_time(14, 55)

def _ensure_datetime(t: Any) -> Optional[datetime]:
    """
    修复从JSON加载后，时间字段为字符串而非datetime的问题
    """
    if isinstance(t, datetime):
        return t
    if isinstance(t, str):
        try:
            return datetime.fromisoformat(t)
        except Exception:
            return None
    return None

def get_limit_up_percent(symbol: str) -> float:
    """获取涨停百分比"""
    if symbol.startswith("SHSE.60") or symbol.startswith("SZSE.00"):
        return MAIN_BOARD_LIMIT_UP_PERCENT
    if symbol.startswith("SZSE.30") or symbol.startswith("SHSE.688"):
        return GEM_BOARD_LIMIT_UP_PERCENT
    if "ST" in symbol or "*ST" in symbol:
        return ST_BOARD_LIMIT_UP_PERCENT
    if symbol.startswith("BSE."):
        return BSE_BOARD_LIMIT_UP_PERCENT
    return MAIN_BOARD_LIMIT_UP_PERCENT

def is_limit_up_price(current_price: float, limit_up_price: float,
                      prev_close: float) -> bool:
    """判断当前价格是否为涨停价（含容忍度）"""
    if prev_close <= 0:
        return False
    tolerance = prev_close * LIMIT_UP_TOLERANCE_PERCENT
    return (limit_up_price - tolerance) <= current_price <= (limit_up_price + tolerance)