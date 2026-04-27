#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM 实盘/模拟盘通用入口
最终版：移除常量硬编码，启动横幅使用 StrategyConfig，全量 logger。
"""
from __future__ import annotations
import os
import sys
import json
import threading
import time
import logging
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

from config.account import (
    ACCOUNT_ID,
    ACCOUNT_DATA_EXPORT_ENABLED,
    ACCOUNT_DATA_EXPORT_INTERVAL,
    ACCOUNT_DATA_EXPORT_DIR,
)
# 只导入入口层实际使用且不在策略配置中的常量
from config.strategy import (
    SYMBOLS_SOURCE,
    MANUAL_SYMBOLS_ENABLED,
    MANUAL_SYMBOLS,
    ENABLE_SLEEP_MODE,
    CALLBACK_ADDITION_ENABLED,
    MIN_TRADE_UNIT,
    CALLBACK_ON_CONDITION2,
    CALLBACK_ON_CONDITION9,
    CALLBACK_ON_CONDITION8,
)
from config.calendar import (
    TRADING_START_TIME,
    ENABLE_TRADING_START_TIME,
    validate_calendar_config,
    STRATEGY_INIT_TIME,
    TRADING_HOURS,
)

from use_case.health_check import is_trading_day, is_in_trading_hours
from use_case.init_assets import build_tracking_symbols
from repository.gm_data_source import load_history_data, get_cash, get_position
from domain.day_data import DayData
from domain.contexts.tick_context import TickContext
from config.strategy.config_objects import load_strategy_config
from service.indicator_service import calculate_indicators
from repository.mail_sender import send_email
from service.order_cancel_service import start_auto_cancel_thread
from adapter.event_handler import on_tick, on_error, on_backtest_finished, on_order_status

from repository.stores import (
    SessionRegistryImpl,
    OrderLedgerImpl,
    BoardStateRepositoryImpl,
    CallbackTaskStoreImpl,
)

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
    """使用策略配置对象打印启动横幅，不再依赖硬编码常量"""
    logger.info("策略初始化开始 @ %s", datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S'))
    logger.info("使用配置的账户ID: %s", ACCOUNT_ID)
    if MANUAL_SYMBOLS_ENABLED and MANUAL_SYMBOLS:
        logger.info("手动输入股票代码: %s", ','.join([s.strip() for s in MANUAL_SYMBOLS if s.strip()]))
    symbols = build_tracking_symbols()
    logger.info("股票代码来源: %s", SYMBOLS_SOURCE)
    logger.info("跟踪股票: %s", ','.join(symbols))
    logger.info("股票总数: %d", len(symbols))
    logger.info("休眠模式: %s", '启用' if ENABLE_SLEEP_MODE else '禁用')
    logger.info("持仓检查: 启用")
    logger.info("账户数据导出: %s", '启用' if ACCOUNT_DATA_EXPORT_ENABLED else '禁用')
    if ACCOUNT_DATA_EXPORT_ENABLED:
        logger.info("导出间隔: %d秒", ACCOUNT_DATA_EXPORT_INTERVAL)
        logger.info("导出目录: %s", ACCOUNT_DATA_EXPORT_DIR)
    logger.info("交易参数配置:")
    logger.info(" 动态回调加仓策略[%s]:", '启用' if CALLBACK_ADDITION_ENABLED else '禁用')
    if CALLBACK_ADDITION_ENABLED:
        logger.info("  最小交易单位: %d股", MIN_TRADE_UNIT)
        logger.info("  条件2卖出后加仓: %s", '是' if CALLBACK_ON_CONDITION2 else '否')
        logger.info("  条件9卖出后加仓: %s", '是' if CALLBACK_ON_CONDITION9 else '否')
        logger.info("  条件8卖出后加仓: %s", '是' if CALLBACK_ON_CONDITION8 else '否')
        logger.info("  机制说明: 基于卖出成交价与昨日收盘价动态计算回调阈值")
        logger.info("  单任务覆盖: 新卖出成交立即覆盖旧加仓任务")
    c2 = config.condition2
    logger.info(" 条件2(动态止盈)[%s]: 触发涨幅=%.1f%%, 回落阈值=%.1f%%",
                '启用' if c2.enabled else '禁用',
                c2.trigger_percent * 100,
                c2.decline_percent * 100)
    c9 = config.condition9
    logger.info(" 条件9(第一区间动态止盈)[%s]: 触发涨幅=%.1f%%, 回落阈值=%.1f%%",
                '启用' if c9.enabled else '禁用',
                c9.trigger_percent * 100,
                c9.decline_percent * 100)
    # 条件4/5/6/7 仍在原配置中，但未纳入 StrategyConfig，暂时保留原打印方式
    from config.strategy import (
        CONDITION4_ENABLED, BUY_BELOW_MA4_QUANTITY,
        CONDITION5_ENABLED, BUY_BELOW_MA8_QUANTITY,
        CONDITION6_ENABLED, BUY_BELOW_MA12_QUANTITY,
        CONDITION7_ENABLED,
    )
    logger.info(" 条件4(低于MA4买入)[%s]: 买入数量=%d", '启用' if CONDITION4_ENABLED else '禁用', BUY_BELOW_MA4_QUANTITY)
    logger.info(" 条件5(低于MA8买入)[%s]: 买入数量=%d", '启用' if CONDITION5_ENABLED else '禁用', BUY_BELOW_MA8_QUANTITY)
    logger.info(" 条件6(低于MA12买入)[%s]: 买入数量=%d", '启用' if CONDITION6_ENABLED else '禁用', BUY_BELOW_MA12_QUANTITY)
    logger.info(" 条件7(14:54后低于MA4卖出)[%s]", '启用' if CONDITION7_ENABLED else '禁用')
    c8 = config.condition8
    logger.info(" 条件8(动态基准价交易)[%s]:", '启用' if c8.enabled else '禁用')
    logger.info("  默认上涨触发=%.1f%%, 默认下跌触发=%.1f%%, 最大交易次数=%d",
                c8.rise_percent * 100, c8.decline_percent * 100, c8.max_trade_times)
    if c8.high_freq_stocks:
        logger.info("  高频股票阈值: 上涨=%.1f%%, 下跌=%.1f%%",
                    c8.high_freq_rise * 100, c8.high_freq_decline * 100)
    if c8.low_freq_stocks:
        logger.info("  低频股票阈值: 上涨=%.1f%%, 下跌=%.1f%%",
                    c8.low_freq_rise * 100, c8.low_freq_decline * 100)
    logger.info("  条件8倍数委托[%s]: 网格间隔=%.1f%%, 最大倍数=%d",
                '启用' if c8.multiple_order_enabled else '禁用',
                c8.grid_interval_percent * 100, c8.max_multiple_limit)

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

    # 创建具体仓库实例
    session_registry = SessionRegistryImpl()
    session_registry.load()
    board_repo = BoardStateRepositoryImpl()
    board_repo.load()
    callback_store = CallbackTaskStoreImpl()
    callback_store.load()
    order_ledger = OrderLedgerImpl()
    order_ledger.load()

    tick_ctx = TickContext(
        session_registry=session_registry,
        board_repo=board_repo,
        callback_store=callback_store,
        order_ledger=order_ledger,
        config=strategy_config,
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
        day_data = session_registry.get(symbol)
        if day_data is None:
            continue
        df = load_history_data(symbol, base_date)
        if df is not None and not df.empty:
            calculate_indicators(df, day_data)

    session_registry.save()
    board_repo.save()
    callback_store.save()
    order_ledger.save()

    subscribe(symbols=symbols, frequency='tick', count=1)
    logger.info("已批量订阅 %d 只股票的tick数据", len(symbols))
    logger.info("策略初始化完成")

    if ACCOUNT_DATA_EXPORT_ENABLED:
        os.makedirs(ACCOUNT_DATA_EXPORT_DIR, exist_ok=True)
        export_path = os.path.join(ACCOUNT_DATA_EXPORT_DIR, "account_data.json")
        cash = get_cash()
        positions = get_position()
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
    start_auto_cancel_thread(order_ledger, session_registry)
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