# domain/day_data.py
# -*- coding: utf-8 -*-
"""纯行情快照对象，不含任何条件内部状态"""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional, Dict, Any


class DayData:
    __slots__ = (
        'symbol',
        'date',
        'open', 'high', 'low', 'close', 'volume',
        'initialized',
        'base_price',  # 开盘基准价（条件2/9使用）
        'ma4', 'ma8', 'ma12', 'cci',  # 技术指标
        'cci_warning_triggered',
        'rise_triggered',
    )

    def __init__(self, symbol: str, base_price: float, current_date: date):
        self.symbol: str = symbol
        self.date: date = current_date
        self.open: Optional[float] = None
        self.high: float = -float('inf')
        self.low: float = float('inf')
        self.close: Optional[float] = None
        self.volume: int = 0
        self.initialized: bool = False
        self.base_price: float = base_price
        self.ma4: Optional[float] = None
        self.ma8: Optional[float] = None
        self.ma12: Optional[float] = None
        self.cci: Optional[float] = None
        self.cci_warning_triggered: bool = False
        self.rise_triggered: int = 0   # 保留少数杂项中仍需的字段（如计数），后续可进一步分离

    def to_dict(self) -> Dict[str, Any]:
        return {slot: getattr(self, slot) for slot in self.__slots__ if slot not in ('symbol', 'date')}

    @classmethod
    def from_dict(cls, symbol: str, data: Dict[str, Any]) -> 'DayData':
        dummy_price = data.get('base_price', 1.0)
        dummy_date = data.get('date')
        if dummy_date is None or isinstance(dummy_date, str):
            dummy_date = date.today()
        obj = cls(symbol, dummy_price, dummy_date)
        # 加载行情字段
        for slot in cls.__slots__:
            if slot in data and slot not in ('symbol', 'date'):
                setattr(obj, slot, data[slot])
        return obj