# tests/unit/test_trade_engine.py
# -*- coding: utf-8 -*-
import sys
from unittest.mock import MagicMock
sys.modules['talib'] = MagicMock()

import unittest
from datetime import datetime, date
from unittest.mock import patch
from domain.day_data import DayData
from service.trade_engine import execute_conditions

class TestTradeEngine(unittest.TestCase):
    def setUp(self):
        # 模拟 TickContext
        mock_ctx = MagicMock()
        mock_ctx.session_registry.get_total_sell_times.return_value = 0
        mock_ctx.board_repo = MagicMock()
        mock_ctx.callback_store = MagicMock()
        mock_ctx.order_ledger = MagicMock()
        mock_ctx.config = MagicMock()
        # 让 board_status 返回安全值
        mock_board_status = MagicMock()
        mock_board_status.get_break_state.return_value = None
        mock_ctx.board_repo.get_board_status.return_value = mock_board_status
        # 设置上下文，使其不会进入重判定分支
        mock_ctx.session_registry.get_condition2.return_value = MagicMock(
            recheck_after_cancel=False, post_cancel_rechecked=False,
            dynamic_profit_triggered=False
        )
        mock_ctx.session_registry.get_condition9.return_value = MagicMock(
            recheck_after_cancel=False, post_cancel_rechecked=False,
            condition9_triggered=False
        )
        self.ctx = mock_ctx

        self.symbol = "SZSE.002842"
        self.day_data = DayData(self.symbol, 10.0, date.today())
        self.day_data.initialized = True
        self.day_data.ma4 = 9.8
        self.tick_time = datetime(2026, 4, 15, 10, 0, 0)

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
            self.ctx
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
                self.ctx
            )
            mock_board.assert_not_called()


if __name__ == "__main__":
    unittest.main()