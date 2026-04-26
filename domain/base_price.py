# -*- coding: utf-8 -*-
"""
动态回调加仓任务实体，替代原金字塔加仓数据结构
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, Optional


class CallbackAdditionTask:
    """
    动态回调加仓任务

    基于单笔有效卖出成交数据动态生成的回调加仓任务，遵循单任务覆盖原则。
    """
    __slots__ = (
        'sell_price',  # 卖出基准价（成交均价）
        'prev_close',  # 昨日收盘价
        'sell_amount',  # 卖出总金额
        'sell_quantity',  # 卖出股数
        'condition_type',  # 来源条件类型（condition2/condition9/condition8等）
        'created_at',  # 任务创建时间
        'is_active',  # 任务是否有效（未被覆盖）
        'callback_threshold',  # 回调阈值 R
        'trigger_price',  # 买入触发价格
        'buy_quantity',  # 计划买入股数
    )

    def __init__(self, sell_price: float, prev_close: float,
                 sell_amount: float, sell_quantity: int,
                 condition_type: str, created_at: Optional[datetime] = None) -> None:
        self.sell_price = sell_price
        self.prev_close = prev_close
        self.sell_amount = sell_amount
        self.sell_quantity = sell_quantity
        self.condition_type = condition_type
        self.created_at = created_at or datetime.now()
        self.is_active = True

        # 计算回调阈值 R = (P_sell - P_prev_close) / P_prev_close
        if prev_close > 0:
            self.callback_threshold = (sell_price - prev_close) / prev_close
        else:
            self.callback_threshold = 0.0

        # 计算买入触发价 P_trigger = P_sell * (1 - R)
        self.trigger_price = sell_price * (1 - self.callback_threshold)

        # 计算买入股数 Q = (M_sell / P_trigger) 向下取整到100股
        if self.trigger_price > 0:
            raw_qty = self.sell_amount / self.trigger_price
            self.buy_quantity = int(raw_qty // 100) * 100
        else:
            self.buy_quantity = 0

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'sell_price': self.sell_price,
            'prev_close': self.prev_close,
            'sell_amount': self.sell_amount,
            'sell_quantity': self.sell_quantity,
            'condition_type': self.condition_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'callback_threshold': self.callback_threshold,
            'trigger_price': self.trigger_price,
            'buy_quantity': self.buy_quantity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CallbackAdditionTask':
        """从字典反序列化"""
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except:
                created_at = None

        task = cls(
            sell_price=data.get('sell_price', 0.0),
            prev_close=data.get('prev_close', 0.0),
            sell_amount=data.get('sell_amount', 0.0),
            sell_quantity=data.get('sell_quantity', 0),
            condition_type=data.get('condition_type', ''),
            created_at=created_at
        )
        task.is_active = data.get('is_active', True)
        return task

    def is_triggered(self, current_price: float) -> bool:
        """检查是否触发买入条件"""
        if not self.is_active or self.buy_quantity <= 0:
            return False
        return current_price <= self.trigger_price

    def complete(self) -> None:
        """标记任务完成（已触发买入）"""
        self.is_active = False


def calculate_trigger_prices(sell_price: float, prev_close: float) -> float:
    """
    计算动态回调加仓的买入触发价格

    Args:
        sell_price: 卖出成交价
        prev_close: 昨日收盘价

    Returns:
        买入触发价格
    """
    if prev_close <= 0:
        return 0.0
    r = (sell_price - prev_close) / prev_close
    return sell_price * (1 - r)


def calculate_callback_buy_quantity(sell_amount: float, trigger_price: float) -> int:
    """
    计算回调加仓买入数量

    Args:
        sell_amount: 卖出总金额
        trigger_price: 买入触发价

    Returns:
        买入股数（已向下取整到100股）
    """
    if trigger_price <= 0:
        return 0
    raw_qty = sell_amount / trigger_price
    return int(raw_qty // 100) * 100