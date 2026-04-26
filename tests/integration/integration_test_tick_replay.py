# tests/integration/test_tick_replay.py
# -*- coding: utf-8 -*-
"""
集成测试：使用模拟 tick 序列回放，验证各条件在真实价格走势下的表现。
"""
import sys
from unittest.mock import MagicMock, patch
sys.modules['talib'] = MagicMock()          # 避免 talib 导入失败
sys.modules['gm'] = MagicMock()             # 避免 gm.api 导入
sys.modules['gm.api'] = MagicMock()
sys.modules['gm.model'] = MagicMock()
sys.modules['gm.pb'] = MagicMock()

import unittest
from datetime import datetime, date
import pytz
from domain.day_data import DayData
from domain.stores import SessionRegistry, BoardStateRepository, CallbackTaskStore, OrderLedger
from service.trade_engine import execute_conditions
from service.tick_data_service import update_day_data, refresh_indicators
from repository.gm_data_source import get_available_position

CN_TZ = pytz.timezone("Asia/Shanghai")

class TestTickReplay(unittest.TestCase):
    def setUp(self):
        # 初始化仓库实例
        self.session_registry = SessionRegistry()
        self.board_repo = BoardStateRepository()
        self.callback_store = CallbackTaskStore()
        self.order_ledger = OrderLedger()

        self.symbol = "SZSE.002842"
        # 设定初始基准价与昨日收盘
        self.base_price = 10.0
        self.prev_close = 9.9

        # 创建 DayData（新交易日）
        self.day_data = DayData(self.symbol, self.base_price, date.today())
        self.day_data.initialized = True
        self.day_data.ma4 = 9.8  # 模拟技术指标
        self.session_registry.set(self.symbol, self.day_data)

        # 初始化 BoardStatus（涨停相关）
        board_status = self.board_repo.get_board_status(self.symbol)
        board_status.prev_close = self.prev_close
        board_status.limit_up_price = round(self.prev_close * 1.1, 2)  # 涨停价 10.89

        # Mock 可用持仓
        patcher = patch('repository.gm_data_source.get_available_position', return_value=5000)
        self.mock_avail = patcher.start()
        self.addCleanup(patcher.stop)

        # Mock 下单函数，记录挂单调用
        patcher_sell = patch('service.order_executor.place_sell')
        self.mock_sell = patcher_sell.start()
        self.addCleanup(patcher_sell.stop)

        patcher_buy = patch('service.order_executor.place_buy')
        self.mock_buy = patcher_buy.start()
        self.addCleanup(patcher_buy.stop)

        # Mock 历史数据加载，避免因没有数据而报错
        patcher_hist = patch('repository.gm_data_source.load_history_data', return_value=None)
        self.mock_hist = patcher_hist.start()
        self.addCleanup(patcher_hist.stop)

        # 重写 tick 模拟中的指标刷新（不依赖真实历史数据）
        self.original_refresh = refresh_indicators
        self.refresh_patcher = patch('service.tick_data_service.refresh_indicators',
                                     lambda sym, dd: None)
        self.refresh_patcher.start()
        self.addCleanup(self.refresh_patcher.stop)

    def _process_tick(self, price, tick_time):
        """模拟一个 tick 到来并处理"""
        tick = {
            'symbol': self.symbol,
            'price': price,
            'cum_volume': 0,
            'created_at': tick_time  # 必须是带时区的 datetime
        }
        # 更新 DayData
        day_data = update_day_data(self.symbol, tick, tick_time.date(), self.session_registry)
        # 打印快照（可选）
        from service.tick_data_service import print_tick_snapshot
        print_tick_snapshot(self.symbol, price, day_data)

        # 执行条件
        execute_conditions(
            self.symbol, price, tick_time,
            get_available_position(self.symbol),
            day_data, day_data.base_price,
            board_repo=self.board_repo,
            callback_store=self.callback_store,
            order_ledger=self.order_ledger,
            session_registry=self.session_registry
        )

    def test_dynamic_profit_trigger_sequence(self):
        """
        场景：股票开盘后缓慢上涨，触发条件2动态止盈监控，然后回落跌破止盈线，触发卖出。
        期间条件8（网格）因为阈值较大不会触发，条件9因为区间未突破也不触发。
        """
        tick_time = datetime(2026, 4, 15, 9, 31, 0, tzinfo=CN_TZ)

        # 价格序列：从 10.0 开始，逐渐上涨到 10.08，最后下跌到 10.05
        prices = [10.0, 10.02, 10.04, 10.06, 10.08, 10.07, 10.06, 10.05]
        for i, price in enumerate(prices):
            self._process_tick(price, tick_time)
            tick_time = tick_time.replace(second=(tick_time.second + 3) % 60)

        # 检查条件2是否触发了卖出
        self.assertTrue(self.mock_sell.called, "条件2动态止盈应该触发卖出")
        # 获取第一次卖出调用的参数
        args, kwargs = self.mock_sell.call_args
        self.assertEqual(kwargs.get('condition_type'), 'condition2',
                         "卖出类型应为 condition2")

    def test_limit_up_board_counting(self):
        """
        场景：股价涨停，验证板数计数。
        """
        tick_time = datetime(2026, 4, 15, 9, 35, 0, tzinfo=CN_TZ)
        # 涨停价 10.89
        self._process_tick(10.89, tick_time)

        # 检查板数
        board_count = self.board_repo.get_board_count_data(self.symbol)
        self.assertIsNotNone(board_count, "应记录板数数据")
        self.assertEqual(board_count.count, 1, "首板计数应为1")

    def test_condition8_grid_not_triggered_by_small_move(self):
        """
        场景：股价小幅波动，未达到条件8的网格阈值，不触发交易。
        """
        tick_time = datetime(2026, 4, 15, 10, 0, 0, tzinfo=CN_TZ)
        # 基准价 10.0，条件8默认阈值 10%，小波动不会触发
        self._process_tick(10.05, tick_time)  # 上涨 0.5%
        self.assertFalse(self.mock_sell.called and self.mock_buy.called,
                         "小波动不应触发条件8")

    def tearDown(self):
        # 清理仓库保存产生的副作用（测试结束后不保留状态文件）
        self.session_registry._gw.clear_all()


if __name__ == '__main__':
    unittest.main()