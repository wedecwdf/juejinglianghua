# -*- coding: utf-8 -*-
"""
日历/时间相关配置集中管理
支持 .env 覆盖，带格式验证
"""
import os
from datetime import date, datetime
from dotenv import load_dotenv

# 确保 .env 已加载
load_dotenv()

# ========== 策略初始化时间配置 ==========
STRATEGY_INIT_TIME: str = os.getenv(
    "STRATEGY_INIT_TIME", "09:25:00"
)  # 格式 HH:MM:SS

# ========== 交易时间段配置 ==========
TRADING_HOURS: dict[str, dict[str, tuple[int, int]]] = {
    'morning': {'start': (9, 30), 'end': (11, 31)},   # 上午交易时段: 9:30-11:31
    'afternoon': {'start': (12, 59), 'end': (15, 31)} # 下午交易时段: 12:59-15:31
}

# ========== 休眠时间段配置 ==========
SLEEP_SCHEDULE: dict[str, tuple[int, int]] = {
    'morning_end': (11, 31),    # 上午结束时间
    'afternoon_start': (12, 59),# 下午开始时间
    'evening_end': (15, 1)      # 全天结束时间
}

# ========== 自动唤醒配置 ==========
WAKEUP_CHECK_INTERVAL: int = 60   # 休眠期间唤醒检查间隔(秒)
NEXT_DAY_CHECK_INTERVAL: int = 300# 检查下一个交易日的间隔(秒)

# ========== 用户可自定义交易开始时间 ==========
TRADING_START_TIME: str = os.getenv(
    "TRADING_START_TIME", "09:30:00"
)  # 格式 HH:MM:SS
ENABLE_TRADING_START_TIME: bool = (
    os.getenv("ENABLE_TRADING_START_TIME", "true").lower() == "true"
)

# -------------------- 配置验证函数 --------------------
def validate_calendar_config() -> None:
    """运行时验证所有日历配置格式合法性"""
    # 验证 STRATEGY_INIT_TIME
    try:
        datetime.strptime(STRATEGY_INIT_TIME, "%H:%M:%S")
    except ValueError:
        raise ValueError(
            f"STRATEGY_INIT_TIME 格式错误: {STRATEGY_INIT_TIME}，应为 HH:MM:SS"
        )
    # 验证 TRADING_START_TIME
    try:
        datetime.strptime(TRADING_START_TIME, "%H:%M:%S")
    except ValueError:
        raise ValueError(
            f"TRADING_START_TIME 格式错误: {TRADING_START_TIME}，应为 HH:MM:SS"
        )
    # 可扩展：验证 TRADING_START_TIME 是否在交易时段内
    start_hour, start_minute, _ = map(int, TRADING_START_TIME.split(':'))
    morning_start = TRADING_HOURS['morning']['start']
    afternoon_start = TRADING_HOURS['afternoon']['start']
    in_morning = (
        start_hour > morning_start[0] or
        (start_hour == morning_start[0] and start_minute >= morning_start[1])
    )
    in_afternoon = (
        start_hour > afternoon_start[0] or
        (start_hour == afternoon_start[0] and start_minute >= afternoon_start[1])
    )
    if not (in_morning or in_afternoon):
        print(f"警告: TRADING_START_TIME {TRADING_START_TIME} 不在交易时段内")