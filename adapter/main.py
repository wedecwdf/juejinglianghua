#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM 实盘/模拟盘通用入口
重构后：仓库注入，共享实例。
"""
from __future__ import annotations
import os
import sys
import json
import threading
import time
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
from config.strategy import (
    MAX_CONDITION8_TRADE_TIMES,
    CONDITION8_RISE_PERCENT,
    CONDITION8_DECLINE_PERCENT,
    CONDITION8_SELL_QUANTITY,
    CONDITION8_BUY_QUANTITY,
    CONDITION8_PRICE_BAND_ENABLED,
    CONDITION8_UPPER_BAND_PERCENT,
    CONDITION8_LOWER_BAND_PERCENT,
    CONDITION8_MULTIPLE_ORDER_ENABLED,
    CONDITION8_GRID_INTERVAL_PERCENT,
    CONDITION8_MAX_MULTIPLE_LIMIT,
    CONDITION8_HIGH_FREQ_GRID_INTERVAL,
    CONDITION8_LOW_FREQ_GRID_INTERVAL,
    CONDITION8_HIGH_FREQ_RISE_PERCENT,
    CONDITION8_HIGH_FREQ_DECLINE_PERCENT,
    CONDITION8_LOW_FREQ_RISE_PERCENT,
    CONDITION8_LOW_FREQ_DECLINE_PERCENT,
    HIGH_FREQUENCY_STOCKS,
    LOW_FREQUENCY_STOCKS,
    SYMBOLS_SOURCE,
    MANUAL_SYMBOLS_ENABLED,
    MANUAL_SYMBOLS,
    ENABLE_SLEEP_MODE,
    CALLBACK_ADDITION_ENABLED,
    MIN_TRADE_UNIT,
    CALLBACK_ON_CONDITION2,
    CALLBACK_ON_CONDITION9,
    CALLBACK_ON_CONDITION8,
    CONDITION2_ENABLED,
    CONDITION2_TRIGGER_PERCENT,
    CONDITION2_DECLINE_PERCENT,
    CONDITION2_SELL_PRICE_OFFSET,
    CONDITION2_DYNAMIC_LINE_THRESHOLD,
    CONDITION2_SELL_PERCENT_HIGH,
    CONDITION2_SELL_PERCENT_LOW,
    CONDITION9_ENABLED,
    CONDITION9_UPPER_BAND_PERCENT,
    CONDITION9_LOWER_BAND_PERCENT,
    CONDITION9_TRIGGER_PERCENT,
    CONDITION9_DECLINE_PERCENT,
    CONDITION9_SELL_PRICE_OFFSET,
    CONDITION9_DYNAMIC_LINE_THRESHOLD,
    CONDITION9_SELL_PERCENT_HIGH,
    CONDITION9_SELL_PERCENT_LOW,
    CONDITION4_ENABLED,
    BUY_BELOW_MA4_QUANTITY,
    CONDITION5_ENABLED,
    BUY_BELOW_MA8_QUANTITY,
    CONDITION6_ENABLED,
    BUY_BELOW_MA12_QUANTITY,
    CONDITION7_ENABLED,
)
from config.calendar import (
    TRADING_START_TIME,
    ENABLE_TRADING_START_TIME,
    validate_calendar_config,
    STRATEGY_INIT_TIME,
    TRADING_HOURS
)

from use_case.health_check import is_trading_day, is_in_trading_hours
from use_case.init_assets import build_tracking_symbols
from repository.gm_data_source import load_history_data, get_cash, get_position
from domain.day_data import DayData
from domain.stores import SessionRegistry, BoardStateRepository, CallbackTaskStore, OrderLedger
from service.indicator_service import calculate_indicators
from repository.mail_sender import send_email
from service.order_cancel_service import start_auto_cancel_thread
from adapter.event_handler import on_tick, on_error, on_backtest_finished, on_order_status, init_repos

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
        print(f"python sdk version: 3.0.178")
        print(f"c sdk version: 3.8.8")
        print("-" * 50)
        print(f"程序启动时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        if is_trading_day(now.date()):
            print(f"当前日期 {now.strftime('%Y-%m-%d')} 是交易日")
        else:
            print(f"当前日期 {now.strftime('%Y-%m-%d')} 不是交易日")
        if is_in_trading_hours(now):
            print(f"当前时间 {now.strftime('%H:%M:%S')} 在交易时段内")
        else:
            print(f"当前时间 {now.strftime('%H:%M:%S')} 不在交易时段内")
        _startup_info_printed = True

def print_strategy_init_banner() -> None:
    print(f"策略初始化开始 @ {datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"使用配置的账户ID: {ACCOUNT_ID}")
    if MANUAL_SYMBOLS_ENABLED and MANUAL_SYMBOLS:
        print(f"手动输入股票代码: {','.join([s.strip() for s in MANUAL_SYMBOLS if s.strip()])}")
    symbols = build_tracking_symbols()
    print(f"股票代码来源: {SYMBOLS_SOURCE}")
    print(f"跟踪股票: {','.join(symbols)}")
    print(f"股票总数: {len(symbols)}")
    print(f"休眠模式: {'启用' if ENABLE_SLEEP_MODE else '禁用'}")
    print(f"持仓检查: 启用")
    print(f"账户数据导出: {'启用' if ACCOUNT_DATA_EXPORT_ENABLED else '禁用'}")
    if ACCOUNT_DATA_EXPORT_ENABLED:
        print(f"导出间隔: {ACCOUNT_DATA_EXPORT_INTERVAL}秒")
        print(f"导出目录: {ACCOUNT_DATA_EXPORT_DIR}")
    print("交易参数配置:")
    print(f" 动态回调加仓策略[{'启用' if CALLBACK_ADDITION_ENABLED else '禁用'}]:")
    if CALLBACK_ADDITION_ENABLED:
        print(f" 最小交易单位: {MIN_TRADE_UNIT}股")
        print(f" 条件2卖出后加仓: {'是' if CALLBACK_ON_CONDITION2 else '否'}")
        print(f" 条件9卖出后加仓: {'是' if CALLBACK_ON_CONDITION9 else '否'}")
        print(f" 条件8卖出后加仓: {'是' if CALLBACK_ON_CONDITION8 else '否'}")
        print(f" 机制说明: 基于卖出成交价与昨日收盘价动态计算回调阈值")
        print(f" 单任务覆盖: 新卖出成交立即覆盖旧加仓任务")
    print(f" 条件2(动态止盈)[{'启用' if CONDITION2_ENABLED else '禁用'}]: "
          f"触发涨幅={CONDITION2_TRIGGER_PERCENT*100:.1f}%, "
          f"回落阈值={CONDITION2_DECLINE_PERCENT*100:.1f}%")
    print(f" 条件9(第一区间动态止盈)[{'启用' if CONDITION9_ENABLED else '禁用'}]: "
          f"触发涨幅={CONDITION9_TRIGGER_PERCENT*100:.1f}%, "
          f"回落阈值={CONDITION9_DECLINE_PERCENT*100:.1f}%")
    print(f" 条件4(低于MA4买入)[{'启用' if CONDITION4_ENABLED else '禁用'}]: 买入数量={BUY_BELOW_MA4_QUANTITY}")
    print(f" 条件5(低于MA8买入)[{'启用' if CONDITION5_ENABLED else '禁用'}]: 买入数量={BUY_BELOW_MA8_QUANTITY}")
    print(f" 条件6(低于MA12买入)[{'启用' if CONDITION6_ENABLED else '禁用'}]: 买入数量={BUY_BELOW_MA12_QUANTITY}")
    print(f" 条件7(14:54后低于MA4卖出)[{'启用' if CONDITION7_ENABLED else '禁用'}]")
    print(f" 条件8(动态基准价交易)[启用]: ")
    print(f" 默认上涨触发={CONDITION8_RISE_PERCENT*100:.1f}%, "
          f"默认下跌触发={CONDITION8_DECLINE_PERCENT*100:.1f}%, "
          f"最大交易次数={MAX_CONDITION8_TRADE_TIMES}")
    if HIGH_FREQUENCY_STOCKS:
        print(f" 高频股票阈值: 上涨={CONDITION8_HIGH_FREQ_RISE_PERCENT*100:.1f}%, "
              f"下跌={CONDITION8_HIGH_FREQ_DECLINE_PERCENT*100:.1f}%")
    if LOW_FREQUENCY_STOCKS:
        print(f" 低频股票阈值: 上涨={CONDITION8_LOW_FREQ_RISE_PERCENT*100:.1f}%, "
              f"下跌={CONDITION8_LOW_FREQ_DECLINE_PERCENT*100:.1f}%")
    print(f" 条件8倍数委托[{'启用' if CONDITION8_MULTIPLE_ORDER_ENABLED else '禁用'}]: "
          f"网格间隔={CONDITION8_GRID_INTERVAL_PERCENT*100:.1f}%, "
          f"最大倍数={CONDITION8_MAX_MULTIPLE_LIMIT}")

def _daily_init_thread():
    while True:
        now = datetime.now(beijing_tz)
        if now.hour == 9 and now.minute == 29 and now.second == 0:
            symbols = build_tracking_symbols()
            if symbols:
                subscribe(symbols=symbols, frequency='tick', count=1)
                print(f"【daily_init】重新订阅行情：{','.join(symbols)}")
            else:
                print("【daily_init】无标的可订阅")
            time.sleep(1)
        time.sleep(1)

def real_init(context):
    validate_calendar_config()
    print_strategy_init_banner()
    print("开始加载持久化数据...")

    # 创建仓库实例（进程级共享）
    session_registry = SessionRegistry()
    session_registry.load()
    board_repo = BoardStateRepository()
    board_repo.load()
    callback_store = CallbackTaskStore()
    callback_store.load()
    order_ledger = OrderLedger()
    order_ledger.load()

    # 注入到事件处理器，确保 on_tick 等使用同一组实例
    init_repos(session_registry, board_repo, callback_store, order_ledger)

    symbols = build_tracking_symbols()
    if not symbols:
        symbols = ["SZSE.002842", "SZSE.002513"]

    base_date = date.today()
    for symbol in symbols:
        df = load_history_data(symbol, base_date)
        if df is not None and not df.empty:
            last_row = df.iloc[-1]
            real_base_price = float(last_row["close"])
            print(f"加载 {symbol} 历史数据成功: {len(df)}条, 真实收盘价: {real_base_price:.4f}")
        else:
            print(f"获取 {symbol} 历史数据失败，使用默认基准价 1.0")
            real_base_price = 1.0

        day_data = DayData(symbol, real_base_price, base_date)
        day_data.initialized = True
        session_registry.set(symbol, day_data)

    print("开始计算技术指标...")
    for symbol in symbols:
        day_data = session_registry.get(symbol)
        if day_data is None:
            continue
        df = load_history_data(symbol, base_date)
        if df is not None and not df.empty:
            calculate_indicators(df, day_data)

    # 保存初始状态
    session_registry.save()
    board_repo.save()
    callback_store.save()
    order_ledger.save()

    subscribe(symbols=symbols, frequency='tick', count=1)
    print(f"已批量订阅 {len(symbols)} 只股票的tick数据")
    print("策略初始化完成")

    if ACCOUNT_DATA_EXPORT_ENABLED:
        os.makedirs(ACCOUNT_DATA_EXPORT_DIR, exist_ok=True)
        export_path = os.path.join(ACCOUNT_DATA_EXPORT_DIR, "account_data.json")
        cash = get_cash()
        positions = get_position()
        data = {"timestamp": datetime.now().isoformat(), "cash": cash, "positions": positions}
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=_json_default)
        print(f"账户数据已导出到: {export_path}")

    # 收盘线程，捕获仓库实例
    def _daily_close():
        while True:
            now = datetime.now(beijing_tz)
            if now.hour == 15 and now.minute == 30 and now.second == 0:
                from use_case.handle_close import handle_market_close
                symbols = build_tracking_symbols()
                for sym in symbols:
                    handle_market_close(sym, now,
                                        session_registry, board_repo, callback_store, order_ledger)
                print("【daily_close】15:30 收盘处理完成")
                time.sleep(1)
            time.sleep(1)

    threading.Thread(target=_daily_init_thread, daemon=True).start()
    threading.Thread(target=_daily_close, daemon=True).start()
    start_auto_cancel_thread(order_ledger, session_registry)
    print("【init】已启动 09:29 重新订阅、15:30 收盘处理、自动撤单守护线程")

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
            print("[EXIT] 无法计算下一个初始化时刻，程序终止。")
            raise SystemExit(1)
        wait_seconds = (next_start - now).total_seconds()
        print(f"[WAIT] 非交易时段，将在 {next_start.strftime('%H:%M:%S')} 自动初始化，还需等待 {int(wait_seconds)} 秒。")
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
        print("收到 Ctrl+C，程序退出")
        from config.logging_config import restore_stdio
        restore_stdio()

if __name__ == "__main__":
    run_strategy()