# use_case/health_check.py
# -*- coding: utf-8 -*-
"""
交易日/时段/休眠判断，无 GM 依赖。
休眠模式开关从环境变量直接读取，不依赖 config.strategy。
"""
from __future__ import annotations
import logging
import os
from datetime import datetime, timedelta, time as dt_time, date
from typing import Optional
import pytz

from config.calendar import (
    TRADING_HOURS,
    SLEEP_SCHEDULE,
    WAKEUP_CHECK_INTERVAL,
    NEXT_DAY_CHECK_INTERVAL,
    TRADING_START_TIME,
    ENABLE_TRADING_START_TIME
)

logger = logging.getLogger(__name__)
beijing_tz = pytz.timezone("Asia/Shanghai")

# 休眠开关直接从环境变量读取，默认启用
ENABLE_SLEEP_MODE: bool = os.getenv('ENABLE_SLEEP_MODE', 'true').lower() == 'true'


def is_trading_day(check_date: date) -> bool:
    try:
        from adapter.gm_adapter import get_trading_dates
        date_str = check_date.strftime("%Y-%m-%d")
        dates = get_trading_dates(start_date=date_str, end_date=date_str)
        return len(dates) > 0
    except Exception as e:
        logger.warning("检查交易日时出错: %s", e)
        return False


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
        logger.info("【休眠模式】程序已唤醒 @ %s", now.astimezone(beijing_tz).strftime('%H:%M:%S'))
        return False
    if not current_sleep and should_sleep(now):
        logger.info("【休眠模式】程序进入休眠 @ %s", now.astimezone(beijing_tz).strftime('%H:%M:%S'))
        return True
    return current_sleep


def ensure_trading_hours_start() -> None:
    beijing_tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(beijing_tz)
    if not is_trading_day(now.date()):
        logger.warning("[EXIT] 今天 (%s) 不是交易日，程序终止。", now.date())
        raise SystemExit(1)
    if not is_in_trading_hours(now):
        next_start = calculate_next_trading_start_time(now)
        if next_start:
            logger.warning("[EXIT] 当前时间 %s 不在交易时段，下一个交易时段开始于 %s，程序终止。",
                           now.strftime('%H:%M:%S'), next_start.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            logger.warning("[EXIT] 当前时间 %s 不在交易时段，程序终止。", now.strftime('%H:%M:%S'))
        raise SystemExit(1)
    logger.info("[OK] 交易时段校验通过，程序继续启动。")


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


def should_start_trading(tick_time: datetime) -> bool:
    if not is_trading_day(tick_time.date()):
        return False
    if not ENABLE_TRADING_START_TIME:
        return True
    start_time = datetime.strptime(TRADING_START_TIME, "%H:%M:%S").time()
    trading_start = beijing_tz.localize(datetime.combine(tick_time.date(), start_time))
    return tick_time >= trading_start


def get_trading_start_datetime(tick_time: datetime) -> Optional[datetime]:
    if not ENABLE_TRADING_START_TIME:
        return None
    start_time = datetime.strptime(TRADING_START_TIME, "%H:%M:%S").time()
    return beijing_tz.localize(datetime.combine(tick_time.date(), start_time))