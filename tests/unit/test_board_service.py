# tests/unit/test_board_service.py
# -*- coding: utf-8 -*-
import sys
from unittest.mock import MagicMock
sys.modules['talib'] = MagicMock()

import unittest
from datetime import datetime
from domain.board import BoardStatus
from service.board_service import handle_board_counting
from service.board.state_machine import get_limit_up_percent, is_limit_up_price

class TestBoardService(unittest.TestCase):
    def test_limit_up_percent(self):
        self.assertEqual(get_limit_up_percent("SHSE.600000"), 0.10)
        self.assertEqual(get_limit_up_percent("SZSE.300001"), 0.20)

    def test_is_limit_up_price(self):
        prev_close = 10.0
        limit_up = 11.0
        self.assertTrue(is_limit_up_price(11.0, limit_up, prev_close))
        self.assertTrue(is_limit_up_price(10.98, limit_up, prev_close))
        self.assertFalse(is_limit_up_price(10.5, limit_up, prev_close))

    def test_first_board_counting(self):
        board_status = BoardStatus()
        tick_time = datetime(2026, 4, 15, 9, 35, 0)
        result = handle_board_counting("SHSE.600000", 11.0, 10.0, tick_time, board_status, None)
        self.assertIsNotNone(result)
        self.assertEqual(result.count, 1)

    def test_not_limit_up_counting(self):
        board_status = BoardStatus()
        tick_time = datetime(2026, 4, 15, 10, 0, 0)
        result = handle_board_counting("SHSE.600000", 10.5, 10.0, tick_time, board_status, None)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
