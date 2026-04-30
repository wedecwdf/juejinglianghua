#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM 实盘/模拟盘通用入口
完全使用配置对象，无旧常量导入。
"""
from __future__ import annotations
import os, sys, json, threading, time, logging
from datetime import datetime, date, timedelta
from pathlib import Path
from gm.api import run, MODE_LIVE, ADJUST_PREV, set_token, subscribe
import pytz

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env", override=True)

_startup_info_printed = False
_startup_lock = threading.Lock()
from config.account import ACCOUNT_ID
from config.calendar import (
    validate_calendar_config, STRATEGY_INIT_TIME,
)
from use_case.health_check import is_trading_day, is_in_trading_hours
from use_case.init_assets import build_tracking_symbols
from adapter.gm_adapter import load_history_data, fetch_cash, fetch_positions
from domain.day_data import DayData
from domain.contexts.tick_context import TickContext
from domain.stores.context_store import ContextStore
from config.strategy.config_objects import load_strategy_config
from service.indicator_service import calculate_indicators
from repository.mail_sender import send_email
from service.order_cancel_service import start_auto_cancel_thread
from adapter.event_handler import on_tick, on_error, on_backtest_finished, on_order_status
from repository.stores import (
    SessionRegistryImpl, OrderLedgerImpl, BoardStateRepositoryImpl, CallbackTaskStoreImpl,
)
from domain.conditions.next_day_stop_loss import NextDayStopLossCondition
from domain.conditions.condition2 import Condition2Condition
from domain.conditions.condition9 import Condition9Condition
from domain.conditions.board import BoardCountingCondition, BoardBreakSellCondition
from domain.conditions.ma import MaTradingCondition
from domain.conditions.condition8_grid import Condition8GridCondition
from domain.conditions.pyramid_profit import PyramidProfitCondition
from domain.conditions.pyramid_add import PyramidAddCondition

logger = logging.getLogger(__name__)
beijing_tz = pytz.timezone("Asia/Shanghai")

def _json_default(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    raise TypeError

def print_startup_info() -> None:
    global _startup_info_printed
    with _startup_lock:
        if _startup_info_printed:
            return
        from config.logging_config import setup_global_logging
        setup_global_logging()
        now = datetime.now(beijing_tz)
        set_token(os.getenv("GM_TOKEN", ""))
        logger.info("python sdk version: 3.0.178")
        logger.info("c sdk version: 3.8.8")
        logger.info("-" * 50)
        logger.info("程序启动时间: %s", now.strftime('%Y-%m-%d %H:%M:%S'))
        if is_trading_day(now.date()):
            logger.info("当前日期 %s 是交易日", now.strftime('%Y-%m-%d'))
        else:
            logger.info("当前日期 %s 不是交易日", now.strftime('%Y-%m-%d'))
        if is_in_trading_hours(now):
            logger.info("当前时间 %s 在交易时段内", now.strftime('%H:%M:%S'))
        else:
            logger.info("当前时间 %s 不在交易时段内", now.strftime('%H:%M:%S'))
        _startup_info_printed = True

def print_strategy_init_banner(config) -> None:
    logger.info("策略初始化开始 @ %s", datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S'))
    logger.info("使用配置的账户ID: %s", ACCOUNT_ID)
    if config.entry.manual_symbols_enabled and config.entry.manual_symbols:
        logger.info("手动输入股票代码: %s", ','.join(config.entry.manual_symbols))
    symbols = build_tracking_symbols()
    logger.info("股票代码来源: %s", config.entry.stock_source)
    logger.info("跟踪股票: %s", ','.join(symbols))
    logger.info("股票总数: %d", len(symbols))
    logger.info("休眠模式: %s", '启用' if config.entry.sleep_mode else '禁用')
    logger.info("账户数据导出: %s", '启用' if config.entry.account_data_export_enabled else '禁用')
    if config.entry.account_data_export_enabled:
        logger.info("导出间隔: %d秒", config.entry.account_data_export_interval)
        logger.info("导出目录: %s", config.entry.account_data_export_dir)
    logger.info("交易参数配置:")
    logger.info(" 动态回调加仓策略[%s]:", '启用' if config.callback.enabled else '禁用')
    if config.callback.enabled:
        logger.info("  最小交易单位: %d股", config.callback.min_trade_unit)
        logger.info("  条件2卖出后加仓: %s", '是' if config.callback.on_condition2 else '否')
        logger.info("  条件9卖出后加仓: %s", '是' if config.callback.on_condition9 else '否')
        logger.info("  条件8卖出后加仓: %s", '是' if config.callback.on_condition8 else '否')
    c2 = config.condition2
    logger.info(" 条件2(动态止盈)[%s]: 触发涨幅=%.2f%%, 回落阈值=%.2f%%",
                '启用' if c2.enabled else '禁用', c2.trigger_percent*100, c2.decline_percent*100)
    c9 = config.condition9
    logger.info(" 条件9(第一区间动态止盈)[%s]: 触发涨幅=%.2f%%, 回落阈值=%.2f%%",
                '启用' if c9.enabled else '禁用', c9.trigger_percent*100, c9.decline_percent*100)
    c8 = config.condition8
    logger.info(" 条件8(动态基准价交易)[%s]: 上涨触发=%.2f%%, 下跌触发=%.2f%%, 最大交易次数=%d",
                '启用' if c8.enabled else '禁用', c8.rise_percent*100, c8.decline_percent*100, c8.max_trade_times)
    logger.info("  启用的条件: %s", ', '.join(config.enabled_conditions))

def _daily_init_thread():
    while True:
        now = datetime.now(beijing_tz)
        if now.hour == 9 and now.minute == 29 and now.second == 0:
            symbols = build_tracking_symbols()
            if symbols:
                subscribe(symbols=symbols, frequency='tick', count=1)
                logger.info("【daily_init】重新订阅行情：%s", ','.join(symbols))
            else:
                logger.info("【daily_init】无标的可订阅")
            time.sleep(1)
        time.sleep(1)

def real_init(context):
    validate_calendar_config()
    strategy_config = load_strategy_config()
    print_strategy_init_banner(strategy_config)
    logger.info("开始加载持久化数据...")

    session_registry = SessionRegistryImpl()
    session_registry.load()
    board_repo = BoardStateRepositoryImpl()
    board_repo.load()
    callback_store = CallbackTaskStoreImpl()
    callback_store.load()
    order_ledger = OrderLedgerImpl()
    order_ledger.load()
    context_store = ContextStore()

    condition_classes = {
        'next_day_stop_loss': (NextDayStopLossCondition, 1),
        'condition2': (Condition2Condition, 2),
        'board_break_sell': (BoardBreakSellCondition, 2),
        'condition9': (Condition9Condition, 3),
        'pyramid_add': (PyramidAddCondition, 4),
        'ma_trading': (MaTradingCondition, 5),
        'condition8_grid': (Condition8GridCondition, 6),
        'pyramid_profit': (PyramidProfitCondition, 7),
        'board_counting': (BoardCountingCondition, 100),
    }
    enabled_names = set(strategy_config.enabled_conditions)
    conditions = []
    side_effects = []
    for name in enabled_names:
        if name in condition_classes:
            cls_, prio = condition_classes[name]
            instance = cls_()
            if instance.is_side_effect:
                side_effects.append((prio, instance))
            else:
                conditions.append((prio, instance))
    conditions.sort(key=lambda x: x[0])
    side_effects.sort(key=lambda x: x[0])
    conditions = [c for _, c in conditions]
    side_effects = [c for _, c in side_effects]

    tick_ctx = TickContext(
        session_registry=session_registry,
        board_repo=board_repo,
        callback_store=callback_store,
        order_repo=order_ledger.as_order_repo(),
        condition_trigger_repo=order_ledger.as_condition_trigger_repo(),
        cancel_lock_manager=order_ledger.as_cancel_lock_manager(),
        sleep_state_manager=order_ledger.as_sleep_state_manager(),
        condition8_tracker=order_ledger.as_condition8_tracker(),
        context_store=context_store,
        config=strategy_config,
        conditions=conditions,
        side_effects=side_effects,
    )
    context.tick_ctx = tick_ctx

    symbols = build_tracking_symbols()
    if not symbols:
        symbols = ["SZSE.002842", "SZSE.002513"]

    base_date = date.today()
    for symbol in symbols:
        df = load_history_data(symbol, base_date)
        if df is not None and not df.empty:
            last_row = df.iloc[-1]
            real_base_price = float(last_row["close"])
            logger.info("加载 %s 历史数据成功: %d条, 真实收盘价: %.4f", symbol, len(df), real_base_price)
        else:
            logger.info("获取 %s 历史数据失败，使用默认基准价 1.0", symbol)
            real_base_price = 1.0
        day_data = DayData(symbol, real_base_price, base_date)
        day_data.initialized = True
        session_registry.set(symbol, day_data)

    logger.info("开始计算技术指标...")
    for symbol in symbols:
        dd = session_registry.get(symbol)
        if dd is None:
            continue
        df = load_history_data(symbol, base_date)
        if df is not None and not df.empty:
            calculate_indicators(df, dd)

    session_registry.save()
    board_repo.save()
    callback_store.save()
    order_ledger.save()

    subscribe(symbols=symbols, frequency='tick', count=1)
    logger.info("已批量订阅 %d 只股票的tick数据", len(symbols))
    logger.info("策略初始化完成")

    if strategy_config.entry.account_data_export_enabled:
        os.makedirs(strategy_config.entry.account_data_export_dir, exist_ok=True)
        export_path = os.path.join(strategy_config.entry.account_data_export_dir, "account_data.json")
        cash = fetch_cash()
        positions = fetch_positions()
        data = {"timestamp": datetime.now().isoformat(), "cash": cash, "positions": positions}
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=_json_default)
        logger.info("账户数据已导出到: %s", export_path)

    def _daily_close():
        while True:
            now = datetime.now(beijing_tz)
            if now.hour == 15 and now.minute == 30 and now.second == 0:
                from use_case.handle_close import handle_market_close
                symbols = build_tracking_symbols()
                for sym in symbols:
                    handle_market_close(sym, now, session_registry, board_repo, callback_store, order_ledger)
                logger.info("【daily_close】15:30 收盘处理完成")
                time.sleep(1)
            time.sleep(1)

    threading.Thread(target=_daily_init_thread, daemon=True).start()
    threading.Thread(target=_daily_close, daemon=True).start()
    start_auto_cancel_thread(order_ledger, session_registry, context_store)
    logger.info("【init】已启动 09:29 重新订阅、15:30 收盘处理、自动撤单守护线程")

def calculate_next_trading_start_time(now: datetime):
    now = now.astimezone(beijing_tz)
    today = now.date()
    init_time = datetime.strptime(STRATEGY_INIT_TIME, "%H:%M:%S").time()
    init_today = beijing_tz.localize(datetime.combine(today, init_time))
    if now < init_today:
        return init_today
    for i in range(1, 8):
        next_date = today + timedelta(days=i)
        if is_trading_day(next_date):
            return beijing_tz.localize(datetime.combine(next_date, init_time))
    return None

def init(context):
    print_startup_info()
    now = datetime.now(beijing_tz)
    if is_in_trading_hours(now):
        real_init(context)
    else:
        next_start = calculate_next_trading_start_time(now)
        if next_start is None:
            logger.error("[EXIT] 无法计算下一个初始化时刻，程序终止。")
            raise SystemExit(1)
        wait_seconds = (next_start - now).total_seconds()
        logger.info("[WAIT] 非交易时段，将在 %s 自动初始化，还需等待 %d 秒。",
                     next_start.strftime('%H:%M:%S'), int(wait_seconds))
        threading.Timer(wait_seconds, lambda: real_init(context)).start()

def run_strategy() -> None:
    print_startup_info()
    run(
        strategy_id=os.getenv("STRATEGY_ID", ""),
        filename=os.path.basename(__file__),
        mode=MODE_LIVE,
        token=os.getenv("GM_TOKEN", ""),
        backtest_start_time="2023-10-01 09:00:00",
        backtest_end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=10_000_000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001,
    )
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        logger.info("收到 Ctrl+C，程序退出")
        from config.logging_config import restore_stdio
        restore_stdio()

if __name__ == "__main__":
    run_strategy()