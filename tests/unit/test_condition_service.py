# tests/unit/test_condition_service.py
# -*- coding: utf-8 -*-
import sys
from unittest.mock import MagicMock
sys.modules['talib'] = MagicMock()

import unittest
from datetime import date
from domain.day_data import DayData
from service.condition_service import check_condition2, check_condition9

class TestCondition2(unittest.TestCase):
    def setUp(self):
        self.day_data = DayData("SZSE.002842", 10.0, date.today())
        self.day_data.ma4 = 9.5
        self.day_data.base_price = 10.0

    def test_not_triggered_low_increase(self):
        res = check_condition2(self.day_data, 0.002, 10.02, 10.0)
        self.assertIsNone(res)

    def test_triggered_and_update_line(self):
        res = check_condition2(self.day_data, 0.005, 10.05, 10.0)
        self.assertIsNone(res)
        self.assertTrue(self.day_data.dynamic_profit_triggered)
        self.assertGreater(self.day_data.dynamic_profit_line, 0)

    def test_sell_when_below_profit_line_and_low_increase(self):
        # 启动监控
        check_condition2(self.day_data, 0.006, 10.06, 10.0)
        # 回落至 10.02，涨幅 0.2% (< 0.31%)，触发卖出
        increase = 0.002
        price = 10.02
        res = check_condition2(self.day_data, increase, price, 10.0)
        self.assertIsNotNone(res)
        self.assertEqual(res["reason"], "条件2动态止盈触发")


class TestCondition9(unittest.TestCase):
    def setUp(self):
        self.day_data = DayData("SZSE.002513", 8.0, date.today())
        self.day_data.base_price = 8.0
        self.day_data.condition9_upper_band = 8.0 * 1.02
        self.day_data.condition9_lower_band = 8.0 * 0.999

    def test_stop_when_exceed_upper_band(self):
        res = check_condition9(self.day_data, 0.025, 8.2, 8.0)
        self.assertIsNone(res)
        self.assertTrue(self.day_data.condition9_stopped)

    def test_not_triggered_when_stopped(self):
        self.day_data.condition9_stopped = True
        res = check_condition9(self.day_data, 0.005, 8.04, 8.0)
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()