# tests/unit/test_trade_engine.py
# -*- coding: utf-8 -*-
import sys
from unittest.mock import MagicMock
sys.modules['talib'] = MagicMock()

import unittest
from datetime import datetime, date
from unittest.mock import patch
from domain.day_data import DayData
from domain.decisions import Decision, DecisionType
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
    @patch('service.trade_engine.arbiter.best_decision', return_value=None)
    def test_no_decision_executes_nothing(self, mock_best, mock_should):
        """仲裁器无决策时，不应调用下单函数"""
        execute_conditions(
            self.symbol, 10.5, self.tick_time, 5000,
            self.day_data, self.day_data.base_price,
            self.ctx
        )
        self.ctx.order_ledger.add_pending_order.assert_not_called()

    @patch('use_case.health_check.should_start_trading', return_value=True)
    @patch('service.trade_engine.arbiter.best_decision')
    @patch('service.trade_engine.place_sell')
    def test_sell_decision_dispatched(self, mock_sell, mock_best, mock_should):
        """卖出决策时调用 place_sell"""
        decision = Decision(
            condition_name='condition2',
            decision_type=DecisionType.SELL,
            symbol=self.symbol,
            price=10.2,
            quantity=100,
            reason='条件2触发'
        )
        mock_best.return_value = decision
        execute_conditions(
            self.symbol, 10.5, self.tick_time, 5000,
            self.day_data, self.day_data.base_price,
            self.ctx
        )
        mock_sell.assert_called_once()

    @patch('use_case.health_check.should_start_trading', return_value=True)
    @patch('service.trade_engine.arbiter.best_decision')
    @patch('service.trade_engine.place_buy')
    @patch('service.trade_engine.complete_callback_task')  # 避免 mock 类型问题
    def test_buy_decision_dispatched(self, mock_complete, mock_buy, mock_best, mock_should):
        """买入决策时调用 place_buy"""
        decision = Decision(
            condition_name='callback_addition',
            decision_type=DecisionType.BUY,
            symbol=self.symbol,
            price=9.8,
            quantity=200,
            reason='动态回调加仓'
        )
        mock_best.return_value = decision
        execute_conditions(
            self.symbol, 10.0, self.tick_time, 5000,
            self.day_data, self.day_data.base_price,
            self.ctx
        )
        mock_buy.assert_called_once()

    @patch('use_case.health_check.should_start_trading', return_value=True)
    @patch('service.trade_engine.arbiter.best_decision', return_value=None)
    def test_all_layers_called_via_arbiter(self, mock_best, mock_should):
        """通过 mock 验证仲裁器被调用"""
        execute_conditions(
            self.symbol, 10.5, self.tick_time, 5000,
            self.day_data, self.day_data.base_price,
            self.ctx
        )
        mock_best.assert_called_once()


if __name__ == "__main__":
    unittest.main()