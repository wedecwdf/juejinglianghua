# tests/unit/test_condition_service.py
# -*- coding: utf-8 -*-
import sys
from unittest.mock import MagicMock
sys.modules['talib'] = MagicMock()

import unittest
from datetime import date
from domain.contexts.condition2 import Condition2Context
from domain.contexts.condition9 import Condition9Context
from service.condition_service import check_condition2, check_condition9

class TestCondition2(unittest.TestCase):
    def setUp(self):
        # 直接创建条件上下文，不再使用 DayData 存储条件状态
        self.ctx2 = Condition2Context()
        self.base_price = 10.0

    def test_not_triggered_low_increase(self):
        """涨幅低于配置阈值时不启动监控"""
        # 传入上下文作为第一个参数，config 为 None 即使用默认配置
        res = check_condition2(self.ctx2, 0.002, 10.02, self.base_price)
        self.assertIsNone(res)
        # 确保未触发
        self.assertFalse(self.ctx2.dynamic_profit_triggered)

    def test_triggered_and_update_line(self):
        """涨幅达到阈值时启动监控并设置止盈线"""
        res = check_condition2(self.ctx2, 0.005, 10.05, self.base_price)
        self.assertIsNone(res)
        self.assertTrue(self.ctx2.dynamic_profit_triggered)
        self.assertGreater(self.ctx2.dynamic_profit_line, 0)
        # 止盈线应在 10.05 * (1 - 回落比例) 附近，回落比例来自默认配置
        # 由于配置可能变化，不做精确断言

    def test_sell_when_below_profit_line_and_low_increase(self):
        """涨幅回落至阈值以下且跌破止盈线时触发卖出"""
        # 先启动监控（创新高）
        check_condition2(self.ctx2, 0.006, 10.06, self.base_price)
        # 现在止盈线为 10.06 * (1 - 默认回落比例)
        # 回落到 10.02，涨幅 0.2% (< 触发阈值 0.31%)
        increase = 0.002
        price = 10.02
        res = check_condition2(self.ctx2, increase, price, self.base_price)
        self.assertIsNotNone(res, f"应触发卖出，止盈线={self.ctx2.dynamic_profit_line}")
        self.assertEqual(res["reason"], "条件2动态止盈触发")


class TestCondition9(unittest.TestCase):
    def setUp(self):
        # Condition9Context 在初始化时会根据 base_price 计算区间
        self.base_price = 8.0
        self.ctx9 = Condition9Context(self.base_price)

    def test_stop_when_exceed_upper_band(self):
        """价格突破区间上限，条件9停止监测"""
        res = check_condition9(self.ctx9, 0.025, 8.2, self.base_price)
        self.assertIsNone(res)
        self.assertTrue(self.ctx9.condition9_stopped)

    def test_not_triggered_when_stopped(self):
        """停止后不再触发"""
        self.ctx9.condition9_stopped = True
        res = check_condition9(self.ctx9, 0.005, 8.04, self.base_price)
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()