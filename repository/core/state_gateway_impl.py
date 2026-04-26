# repository/core/state_gateway_impl.py

# -*- coding: utf-8 -*-
"""
StateGateway 真实实现 - 拆分版（Mixin组合）

通过多重继承整合各功能模块，保持对外接口100%兼容

修改点：添加 callback_addition_tasks 存储动态回调加仓任务
"""
from __future__ import annotations
from typing import Optional, Dict, Any, List, Set

# Domain 导入
from domain.day_data import DayData
from domain.board import BoardStatus, BoardBreakStatus, BoardCountData

# Mixin 导入
from repository.persistence.persistence_mixin import _PersistenceMixin
from repository.operations.board_mixin import _BoardMixin
from repository.operations.order_mixin import _OrderMixin
from repository.operations.condition8_mixin import _Condition8Mixin
from repository.operations.rollback_mixin import _RollbackMixin


class _StateGatewayImpl(
    _PersistenceMixin,
    _BoardMixin,
    _OrderMixin,
    _Condition8Mixin,
    _RollbackMixin,
):
    """
    状态网关真实实现
    功能分布：
    - _PersistenceMixin: 所有文件持久化 (save/load/clear)
    - _BoardMixin: 板数/断板/炸板状态获取
    - _OrderMixin: 挂单/条件触发记录/互斥撤单
    - _Condition8Mixin: 条件8特殊逻辑(成交记录、撤单回退、锁)
    - _RollbackMixin: 各类条件的状态回滚
    """
    _instance: Optional["_StateGatewayImpl"] = None

    def __new__(cls) -> "_StateGatewayImpl":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        """初始化所有内存状态容器（各 Mixin 方法依赖这些属性）"""
        # DayData 与交易计数
        self.current_day_data: Dict[str, DayData] = {}
        self.total_buy_quantity: Dict[str, int] = {}

        # 动态回调加仓任务（替代原金字塔加仓基准价）
        self.callback_addition_tasks: Dict[str, Dict[str, Any]] = {}

        # 次日调整机制
        self.dynamic_profit_next_day_adjustment_data: Dict[str, Dict[str, Any]] = {}

        # 板数相关
        self.board_status: Dict[str, BoardStatus] = {}
        self.board_count_data: Dict[str, BoardCountData] = {}
        self.board_break_status: Dict[str, BoardBreakStatus] = {}

        # 订单与触发记录
        self.pending_orders: Dict[str, Dict[str, Any]] = {}
        self.condition_triggers: Dict[str, Dict[str, Any]] = {}

        # 撤单与休眠标记
        self._cancelled_symbols: Set[str] = set()
        self._cancelling_symbols: Set[str] = set()
        self._sleep_state: bool = False

        # 条件8专用双向挂单池
        self.condition8_pending: Dict[str, Dict[str, str]] = {}

        # 启动时加载持久化数据
        self._load_all()