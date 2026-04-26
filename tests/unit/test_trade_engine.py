# tests/unit/test_trade_engine.py
# -*- coding: utf-8 -*-
import sys
from unittest.mock import MagicMock
sys.modules['talib'] = MagicMock()

import unittest
from datetime import datetime, date
from unittest.mock import patch
import pytz
from domain.day_data import DayData
from domain.stores import SessionRegistry, BoardStateRepository, CallbackTaskStore, OrderLedger
from service.trade_engine import execute_conditions

CN_TZ = pytz.timezone("Asia/Shanghai")

class TestTradeEngine(unittest.TestCase):
    def setUp(self):
        self.session_registry = SessionRegistry()
        self.board_repo = BoardStateRepository()
        self.callback_store = CallbackTaskStore()
        self.order_ledger = OrderLedger()
        self.symbol = "SZSE.002842"
        self.day_data = DayData(self.symbol, 10.0, date.today())
        self.day_data.initialized = True
        self.day_data.ma4 = 9.8
        self.session_registry.set(self.symbol, self.day_data)
        board_status = self.board_repo.get_board_status(self.symbol)
        board_status.prev_close = 9.9
        self.tick_time = datetime(2026, 4, 15, 10, 0, 0, tzinfo=CN_TZ)

    # 直接 mock 延迟导入的真实来源
    @patch('use_case.health_check.should_start_trading', return_value=True)
    @patch('service.trade_engine.execute_next_day_stop_loss', return_value=False)
    @patch('service.trade_engine.execute_board_mechanisms', return_value=False)
    @patch('service.trade_engine.execute_pyramid_strategy')
    @patch('service.trade_engine.execute_condition2_profit', return_value=False)
    @patch('service.trade_engine.execute_condition9_profit', return_value=False)
    @patch('service.trade_engine.execute_ma_trading', return_value=False)
    @patch('service.trade_engine.execute_condition8_grid', return_value=False)
    @patch('service.trade_engine.execute_pyramid_profit', return_value=False)
    def test_all_layers_called(self, mock_pyr, mock_grid, mock_ma, mock_c9, mock_c2,
                               mock_pyramid, mock_board, mock_stop, mock_should):
        execute_conditions(
            self.symbol, 10.5, self.tick_time, 5000,
            self.day_data, self.day_data.base_price,
            board_repo=self.board_repo,
            callback_store=self.callback_store,
            order_ledger=self.order_ledger,
            session_registry=self.session_registry
        )
        self.assertTrue(mock_stop.called)
        self.assertTrue(mock_board.called)
        self.assertTrue(mock_pyramid.called)
        self.assertTrue(mock_c2.called)

    @patch('use_case.health_check.should_start_trading', return_value=True)
    @patch('service.trade_engine.execute_next_day_stop_loss', return_value=True)
    def test_layer1_short_circuit(self, mock_stop, mock_should):
        with patch('service.trade_engine.execute_board_mechanisms') as mock_board:
            execute_conditions(
                self.symbol, 10.5, self.tick_time, 5000,
                self.day_data, self.day_data.base_price,
                board_repo=self.board_repo,
                callback_store=self.callback_store,
                order_ledger=self.order_ledger,
                session_registry=self.session_registry
            )
            mock_board.assert_not_called()


if __name__ == "__main__":
    unittest.main()