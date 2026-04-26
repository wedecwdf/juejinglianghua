# -*- coding: utf-8 -*-
"""
所有编号条件检查入口，保持对外接口100%兼容。

【变更】将 check_condition8_pyramid_profit 替换为 check_pyramid_profit
"""

from __future__ import annotations

# 保持原有导入路径兼容 - 从子模块重新导出所有函数
from service.conditions import (
    check_condition2,
    check_condition4,
    check_condition5,
    check_condition6,
    check_condition7,
    check_condition8,
    check_condition9,
    # 【移除兼容层】直接使用独立函数
    check_pyramid_profit,  # 替代原 check_condition8_pyramid_profit
    # 辅助函数如需对外暴露也可导出，通常内部使用即可
    _sell_qty_by_percent,
    _get_stock_frequency_type,
    _get_condition8_thresholds,
    _get_grid_interval_percent,
    _calculate_skipped_grids,
    _calculate_multiple_order_quantity,
)

# 保持 __all__ 明确（可选）
__all__ = [
    'check_condition2',
    'check_condition4',
    'check_condition5',
    'check_condition6',
    'check_condition7',
    'check_condition8',
    'check_condition9',
    'check_pyramid_profit',  # 新名称
]