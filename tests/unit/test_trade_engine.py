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
        mock_ctx = MagicMock()
        mock_ctx.session_registry.get_total_sell_times.return_value = 0
        mock_ctx.board_repo = MagicMock()
        mock_ctx.callback_store = MagicMock()
        mock_ctx.order_ledger = MagicMock()
        mock_ctx.config = MagicMock()
        mock_ctx.context_store = MagicMock()
        # 默认空条件列表和副作用列表
        mock_ctx.conditions = []
        mock_ctx.side_effects = []
        # 获取条件上下文时返回简单对象
        mock_ctx.context_store.get.return_value = MagicMock()
        self.ctx = mock_ctx

        self.symbol = "SZSE.002842"
        self.day_data = DayData(self.symbol, 10.0, date.today())
        self.day_data.initialized = True
        self.day_data.ma4 = 9.8
        self.tick_time = datetime(2026, 4, 15, 10, 0, 0)

    @patch('use_case.health_check.should_start_trading', return_value=True)
    @patch('service.trade_engine.DecisionArbiter.best_decision', return_value=None)
    def test_no_decision_executes_nothing(self, mock_best, mock_should):
        execute_conditions(
            self.symbol, 10.5, self.tick_time, 5000,
            self.day_data, self.day_data.base_price,
            self.ctx
        )
        self.ctx.order_ledger.add_pending_order.assert_not_called()

    @patch('use_case.health_check.should_start_trading', return_value=True)
    @patch('service.trade_engine.DecisionArbiter.best_decision')
    @patch('service.trade_engine.place_sell')
    def test_sell_decision_executes_sell(self, mock_sell, mock_best, mock_should):
        decision = MagicMock(spec=Decision)
        decision.condition_name = 'condition2'
        decision.decision_type = 'sell'
        decision.symbol = self.symbol
        decision.price = 10.2
        decision.quantity = 100
        decision.reason = '条件2触发'
        decision.extra = {}
        mock_best.return_value = decision
        execute_conditions(
            self.symbol, 10.5, self.tick_time, 5000,
            self.day_data, self.day_data.base_price,
            self.ctx
        )
        mock_sell.assert_called_once()

    @patch('use_case.health_check.should_start_trading', return_value=True)
    @patch('service.trade_engine.DecisionArbiter.best_decision')
    @patch('service.trade_engine.place_buy')
    def test_buy_decision_executes_buy(self, mock_buy, mock_best, mock_should):
        decision = MagicMock(spec=Decision)
        decision.condition_name = 'callback_addition'
        decision.decision_type = 'buy'
        decision.symbol = self.symbol
        decision.price = 9.8
        decision.quantity = 200
        decision.reason = '动态回调加仓'
        decision.extra = {}
        mock_best.return_value = decision
        execute_conditions(
            self.symbol, 10.0, self.tick_time, 5000,
            self.day_data, self.day_data.base_price,
            self.ctx
        )
        mock_buy.assert_called_once()

    @patch('use_case.health_check.should_start_trading', return_value=True)
    @patch('service.trade_engine.DecisionArbiter.best_decision')
    @patch('service.trade_engine.place_sell')
    @patch('service.trade_engine.place_buy')
    def test_higher_priority_wins(self, mock_buy, mock_sell, mock_best, mock_should):
        """模拟仲裁器返回第一个决策，确保高优先级条件生效（由仲裁器内部顺序保证）"""
        decision = MagicMock(spec=Decision)
        decision.condition_name = 'next_day_stop_loss'
        decision.decision_type = 'sell'
        decision.symbol = self.symbol
        decision.price = 10.0
        decision.quantity = 500
        decision.reason = '次日止损'
        decision.extra = {}
        mock_best.return_value = decision
        execute_conditions(
            self.symbol, 10.5, self.tick_time, 5000,
            self.day_data, self.day_data.base_price,
            self.ctx
        )
        # 只要 sell 被调用，buy 未被调用即可
        mock_sell.assert_called_once()
        mock_buy.assert_not_called()


if __name__ == "__main__":
    unittest.main()