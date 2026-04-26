# tests/unit/test_pyramid_service.py
# -*- coding: utf-8 -*-
import sys
from unittest.mock import MagicMock
sys.modules['talib'] = MagicMock()
# 解决 protobuf 版本问题需配合环境变量，代码内不再重复处理

import unittest
from domain.base_price import CallbackAdditionTask
from domain.stores import CallbackTaskStore
from service.pyramid_service import (
    add_callback_task, check_callback_strategy,
    complete_callback_task, remove_callback_task,
    should_create_callback_task,
)

class TestPyramidService(unittest.TestCase):
    def setUp(self):
        self.store = CallbackTaskStore()
        self.symbol = "SZSE.002842"
        self.sell_price = 10.5
        self.prev_close = 10.0
        self.sell_amount = 1050.0
        self.sell_quantity = 100
        self.condition_type = "condition2"

    def test_should_create_task(self):
        self.assertTrue(should_create_callback_task("condition2"))
        self.assertFalse(should_create_callback_task("board_dynamic_profit"))

    def test_add_and_trigger(self):
        task = add_callback_task(
            self.symbol, self.sell_price, self.prev_close,
            self.sell_amount, self.sell_quantity, self.condition_type,
            store=self.store
        )
        self.assertTrue(task.is_active)
        result = check_callback_strategy(self.symbol, task.trigger_price - 0.01, store=self.store)
        self.assertIsNotNone(result)

    def test_override(self):
        add_callback_task(
            self.symbol, self.sell_price, self.prev_close,
            self.sell_amount, self.sell_quantity, self.condition_type,
            store=self.store
        )
        add_callback_task(
            self.symbol, 11.0, self.prev_close,
            1100.0, 100, "condition9",
            store=self.store
        )
        new_data = self.store.get_task(self.symbol)
        self.assertEqual(new_data['sell_price'], 11.0)

    def test_complete(self):
        add_callback_task(
            self.symbol, self.sell_price, self.prev_close,
            self.sell_amount, self.sell_quantity, self.condition_type,
            store=self.store
        )
        complete_callback_task(self.symbol, store=self.store)
        self.assertFalse(self.store.get_task(self.symbol)['is_active'])

    def test_remove(self):
        add_callback_task(
            self.symbol, self.sell_price, self.prev_close,
            self.sell_amount, self.sell_quantity, self.condition_type,
            store=self.store
        )
        self.assertTrue(remove_callback_task(self.symbol, store=self.store))

if __name__ == "__main__":
    unittest.main()
