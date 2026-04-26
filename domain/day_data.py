# -*- coding: utf-8 -*-
"""
day_data.py

将原先 strategy 中庞大的 day_data 字典拆成独立、可序列化的类，
保证字段/逻辑/默认值与原文件 100 % 一致，仅访问方式从 dict 改为属性。

【重要变更】将 condition8_pyramid_profit_* 字段重命名为 pyramid_profit_*，
实现与条件8的完全数据独立

【新增】添加动态止盈撤单后重新判定相关字段（condition2/condition9_recheck_after_cancel, post_cancel_rechecked）

【重构】解决上帝对象问题：将约50个字段按业务域拆分为10个独立State子对象，
DayData 改为门面(Facade)类，通过 __getattr__/__setattr__ 保持对外接口100%兼容。
所有外部代码无需修改，调试时可按业务域查看 _state_instances 中的子对象。
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Optional, Dict, Any

# 导入所有状态子对象
from domain.states import (
    MarketState, IndicatorState, Condition2State,
    Condition4To7State, Condition8State, Condition9State,
    MiscState, PyramidState, RecheckState, NextDayState
)


class DayData:
    """
    原 current_day_data[symbol] 的完整对标，所有字段保持原名、同类型、同默认值。

    【内部重构】
    字段实际存储在独立的 State 子对象中，DayData 仅作为门面代理访问。
    调试时可透过 _state_instances 查看各业务域状态，避免数据污染路径难以定位。
    """

    __slots__ = (
        'symbol',  # 股票代码（门面本体属性）
        'date',  # 当前日期（门面本体属性）
        '_state_instances',  # 状态子对象容器
        '_attr_to_state',  # 属性名 -> 状态对象 映射表
    )

    def __init__(self, symbol: str, base_price: float, current_date: date) -> None:
        # 门面本体属性直接设置（绕过 __setattr__ 代理，避免初始化阶段递归）
        object.__setattr__(self, 'symbol', symbol)
        object.__setattr__(self, 'date', current_date)

        # 初始化各业务域状态子对象
        states = {
            'market': MarketState(base_price, current_date),
            'indicator': IndicatorState(),
            'condition2': Condition2State(),
            'condition4_7': Condition4To7State(),
            'condition8': Condition8State(base_price),
            'condition9': Condition9State(base_price),
            'misc': MiscState(),
            'pyramid': PyramidState(base_price),
            'recheck': RecheckState(),
            'next_day': NextDayState(),
        }
        object.__setattr__(self, '_state_instances', states)

        # 构建属性名到状态对象的映射，用于 __getattr__ / __setattr__ 快速路由
        attr_map: Dict[str, Any] = {}
        for state in states.values():
            for slot in state.__slots__:
                attr_map[slot] = state
        object.__setattr__(self, '_attr_to_state', attr_map)

    # ------------------------------------------------------------------ #
    # 门面代理：所有业务字段访问自动路由到对应 State 子对象
    # ------------------------------------------------------------------ #

    def __getattr__(self, name: str) -> Any:
        """属性读取代理：将业务字段访问转发到对应的 State 子对象"""
        # 使用 object.__getattribute__ 避免自身递归
        attr_map = object.__getattribute__(self, '_attr_to_state')
        if name in attr_map:
            state = attr_map[name]
            return getattr(state, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """属性写入代理：将业务字段写入转发到对应的 State 子对象"""
        # 门面本体属性直接写入
        if name in ('symbol', 'date', '_state_instances', '_attr_to_state'):
            super().__setattr__(name, value)
            return

        # 若已初始化完成，且属性属于某 State，则转发
        try:
            attr_map = object.__getattribute__(self, '_attr_to_state')
        except AttributeError:
            attr_map = {}

        if name in attr_map:
            state = attr_map[name]
            setattr(state, name, value)
        else:
            # 不在任何 State 中的属性，按原 DayData 行为抛出 AttributeError
            # （因 __slots__ 限制，无法动态创建新属性）
            super().__setattr__(name, value)

    # ------------------------------------------------------------------ #
    # 序列化 / 反序列化：保证与旧 json 结构 100 % 兼容
    # ------------------------------------------------------------------ #

    def to_dict(self) -> Dict[str, Any]:
        """将所有 State 子对象的字典合并输出，保持与旧 JSON 结构一致"""
        result: Dict[str, Any] = {
            'symbol': self.symbol,
            'date': self.date,
        }
        for state in self._state_instances.values():
            result.update(state.to_dict())
        return result

    @classmethod
    def from_dict(cls, symbol: str, data: Dict[str, Any]) -> 'DayData':
        dummy_price = data.get('base_price', 1.0)
        dummy_date = data.get('date')
        if dummy_date is None or isinstance(dummy_date, str):
            dummy_date = date.today()

        obj = cls(symbol, dummy_price, dummy_date)

        # 【兼容性处理】处理旧数据中的 condition8_pyramid_profit_* 字段名
        if 'condition8_pyramid_profit_status' in data and 'pyramid_profit_status' not in data:
            data['pyramid_profit_status'] = data.pop('condition8_pyramid_profit_status')
        if 'condition8_pyramid_profit_base_price' in data and 'pyramid_profit_base_price' not in data:
            data['pyramid_profit_base_price'] = data.pop('condition8_pyramid_profit_base_price')
        if 'condition8_pyramid_profit_triggered' in data and 'pyramid_profit_triggered' not in data:
            data['pyramid_profit_triggered'] = data.pop('condition8_pyramid_profit_triggered')

        # 处理 date 字段类型转换（兼容字符串日期）
        if 'date' in data:
            d = data['date']
            if isinstance(d, str):
                try:
                    d = datetime.strptime(d, "%Y-%m-%d").date()
                except Exception:
                    d = date.today()
            obj.date = d

        # 让各 State 子对象从字典加载数据（只加载自己认识的字段）
        for state in obj._state_instances.values():
            state.from_dict(data)

        return obj