# -*- coding: utf-8 -*-
"""
交易日/时段/休眠判断，无 GM 依赖
"""
from __future__ import annotations

from datetime import datetime, timedelta, time as dt_time
from typing import Optional

import pytz

# 1. 日历相关配置
from config.calendar import (
    TRADING_HOURS,
    SLEEP_SCHEDULE,
    WAKEUP_CHECK_INTERVAL,
    NEXT_DAY_CHECK_INTERVAL,
    TRADING_START_TIME,
    ENABLE_TRADING_START_TIME
)
# 2. 休眠开关实际在 strategy 模块
from config.strategy import ENABLE_SLEEP_MODE
from repository.gm_data_source import get_trading_dates

beijing_tz = pytz.timezone("Asia/Shanghai")

# ------------------------------------------------------------------交易日
def is_trading_day(check_date: date) -> bool:
    try:
        date_str = check_date.strftime("%Y-%m-%d")
        dates = get_trading_dates(start_date=date_str, end_date=date_str)
        return len(dates) > 0
    except Exception as e:
        print(f"检查交易日时出错: {e}")
        return False

# ------------------------------------------------------------------交易时段
def is_in_trading_hours(now: datetime) -> bool:
    now = now.astimezone(beijing_tz)
    hour, minute = now.hour, now.minute
    morning = TRADING_HOURS["morning"]
    if (hour > morning["start"][0] or (hour == morning["start"][0] and minute >= morning["start"][1])) and \
       (hour < morning["end"][0] or (hour == morning["end"][0] and minute <= morning["end"][1])):
        return True
    afternoon = TRADING_HOURS["afternoon"]
    if (hour > afternoon["start"][0] or (hour == afternoon["start"][0] and minute >= afternoon["start"][1])) and \
       (hour < afternoon["end"][0] or (hour == afternoon["end"][0] and minute <= afternoon["end"][1])):
        return True
    return False

# ------------------------------------------------------------------休眠
def should_sleep(now: datetime) -> bool:
    if not ENABLE_SLEEP_MODE:
        return False
    now = now.astimezone(beijing_tz)
    hour, minute = now.hour, now.minute
    if hour == SLEEP_SCHEDULE["morning_end"][0] and minute >= SLEEP_SCHEDULE["morning_end"][1]:
        return True
    if hour == SLEEP_SCHEDULE["evening_end"][0] and minute >= SLEEP_SCHEDULE["evening_end"][1]:
        return True
    if SLEEP_SCHEDULE["morning_end"][0] < hour < SLEEP_SCHEDULE["afternoon_start"][0]:
        return True
    return False


def should_wakeup(now: datetime) -> bool:
    if not ENABLE_SLEEP_MODE:
        return False
    now = now.astimezone(beijing_tz)
    hour, minute = now.hour, now.minute
    if hour == SLEEP_SCHEDULE["afternoon_start"][0] and minute >= SLEEP_SCHEDULE["afternoon_start"][1]:
        return True
    if hour >= 9:
        return True
    return False


def update_sleep_state(now: datetime, current_sleep: bool) -> bool:
    if not ENABLE_SLEEP_MODE:
        return False
    if current_sleep and should_wakeup(now):
        print(f"【休眠模式】程序已唤醒 @ {now.astimezone(beijing_tz).strftime('%H:%M:%S')}")
        return False
    if not current_sleep and should_sleep(now):
        print(f"【休眠模式】程序进入休眠 @ {now.astimezone(beijing_tz).strftime('%H:%M:%S')}")
        return True
    return current_sleep

# ------------------------------------------------------------------启动时段校验
def ensure_trading_hours_start() -> None:
    """
    必须在交易时段内才能启动，否则直接退出进程。
    供 main.py 启动前调用。
    """
    beijing_tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(beijing_tz)
    if not is_trading_day(now.date()):
        print(f"[EXIT] 今天 ({now.date()}) 不是交易日，程序终止。")
        raise SystemExit(1)
    if not is_in_trading_hours(now):
        next_start = calculate_next_trading_start_time(now)
        if next_start:
            print(f"[EXIT] 当前时间 {now.strftime('%H:%M:%S')} 不在交易时段，下一个交易时段开始于 {next_start.strftime('%Y-%m-%d %H:%M:%S')}，程序终止。")
        else:
            print(f"[EXIT] 当前时间 {now.strftime('%H:%M:%S')} 不在交易时段，程序终止。")
        raise SystemExit(1)
    print(f"[OK] 交易时段校验通过，程序继续启动。")

# ------------------------------------------------------------------工具
def calculate_next_trading_start_time(now: datetime) -> Optional[datetime]:
    now = now.astimezone(beijing_tz)
    today = now.date()
    morning_start = dt_time(*TRADING_HOURS["morning"]["start"])
    afternoon_start = dt_time(*TRADING_HOURS["afternoon"]["start"])
    if is_trading_day(today):
        if now.time() < morning_start:
            return beijing_tz.localize(datetime.combine(today, morning_start))
        if now.time() < afternoon_start:
            return beijing_tz.localize(datetime.combine(today, afternoon_start))
    for i in range(1, 8):
        check_date = today + timedelta(days=i)
        if is_trading_day(check_date):
            return beijing_tz.localize(datetime.combine(check_date, morning_start))
    return None

# ------------------------------------------------------------------新增：带时区、交易日、日志优化的交易开始判断（供 handle_tick 调用）
def should_start_trading(tick_time: datetime) -> bool:
    """
    判断是否应该开始交易
    1. 非交易日 → False
    2. 未启用 → True
    3. 已到达或超过 TRADING_START_TIME → True
    """
    if not is_trading_day(tick_time.date()):
        return False
    if not ENABLE_TRADING_START_TIME:
        return True
    start_time = datetime.strptime(TRADING_START_TIME, "%H:%M:%S").time()
    trading_start = beijing_tz.localize(datetime.combine(tick_time.date(), start_time))
    return tick_time >= trading_start


def get_trading_start_datetime(tick_time: datetime) -> Optional[datetime]:
    """返回当日带时区的交易开始时间对象；未启用时返回 None"""
    if not ENABLE_TRADING_START_TIME:
        return None
    start_time = datetime.strptime(TRADING_START_TIME, "%H:%M:%S").time()
    return beijing_tz.localize(datetime.combine(tick_time.date(), start_time))