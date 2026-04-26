# tests/integration/test_tick_replay.py
# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import MagicMock, patch
sys.modules['talib'] = MagicMock()
sys.modules['gm'] = MagicMock()
sys.modules['gm.api'] = MagicMock()
sys.modules['gm.model'] = MagicMock()
sys.modules['gm.pb'] = MagicMock()

import unittest
from datetime import datetime, date
import pytz
from domain.day_data import DayData
from service.condition_service import check_condition2

CN_TZ = pytz.timezone("Asia/Shanghai")


class TestCondition2Realistic(unittest.TestCase):
    def setUp(self):
        self.symbol = "SZSE.002842"
        self.base_price = 10.0
        self.day_data = DayData(self.symbol, self.base_price, date.today())

    def test_sell_only_when_increase_below_threshold(self):
        """
        真实逻辑：只有当涨幅低于 CONDITION2_TRIGGER_PERCENT 时，
        才检查止盈线。因此价格需回落至接近基准价。
        """
        # 1. 拉高启动监控，高点 10.5
        check_condition2(self.day_data, 0.05, 10.5, 10.0)
        self.assertTrue(self.day_data.dynamic_profit_triggered)

        # 2. 回落至 10.03，涨幅 0.3% (< 0.31%)
        increase = 0.003
        price = 10.03
        res = check_condition2(self.day_data, increase, price, 10.0)
        self.assertIsNotNone(res, "涨幅低于阈值时应触发止盈")
        self.assertEqual(res["reason"], "条件2动态止盈触发")

    def test_no_sell_when_increase_still_high(self):
        """涨幅仍高于阈值时，即使跌破止盈线也不卖出"""
        check_condition2(self.day_data, 0.05, 10.5, 10.0)
        # 回落到 10.3，涨幅 3% > 0.31%，不触发
        res = check_condition2(self.day_data, 0.03, 10.3, 10.0)
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()