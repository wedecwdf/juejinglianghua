# use_case/init_assets.py
# -*- coding: utf-8 -*-

"""
资产合并：持仓 + 手动，返回最终订阅列表
"""

from __future__ import annotations

from typing import List

# 1. ACCOUNT_ID 单独从 account 模块拿
from config.account import ACCOUNT_ID

# 2. 其余变量依旧从 strategy 模块拿
from config.strategy import (
    SYMBOLS_SOURCE,
    MANUAL_SYMBOLS_ENABLED,
    MANUAL_SYMBOLS
)


def get_portfolio_symbols() -> List[str]:
    """持仓代码列表"""
    if not ACCOUNT_ID:
        print("错误: 未配置账户ID")
        return []

    try:
        # 使用 gm.api 的 get_position 函数
        from gm.api import get_position as gm_get_position
        positions = gm_get_position()
        symbols = [pos["symbol"] for pos in positions
                   if pos["volume"] > 0 and pos["side"] == 1]  # PositionSide_Long

        for sym in symbols:
            print(f"发现持仓股票: {sym}, 数量: {next(p['volume'] for p in positions if p['symbol'] == sym)}")
        return symbols
    except Exception as e:
        print(f"获取账户持仓失败: {e}")
        return []


def get_manual_symbols() -> List[str]:
    """手动代码列表"""
    if not MANUAL_SYMBOLS_ENABLED or not MANUAL_SYMBOLS:
        print("手动输入股票代码功能未启用或列表为空")
        return []

    valid = list({s.strip() for s in MANUAL_SYMBOLS if s.strip()})
    print(f"手动输入股票代码: {', '.join(valid)}")
    return valid


def build_tracking_symbols() -> List[str]:
    """按配置模式合并"""
    portfolio = get_portfolio_symbols()
    manual = get_manual_symbols()

    if SYMBOLS_SOURCE == "position":
        symbols = portfolio
        print("股票代码来源: 仅持仓股票")
    elif SYMBOLS_SOURCE == "manual":
        symbols = manual
        print("股票代码来源: 仅手动输入")
    elif SYMBOLS_SOURCE == "both":
        symbols = list(set(portfolio + manual))
        print("股票代码来源: 持仓股票 + 手动输入")
    else:
        print(f"未知的股票代码来源模式: {SYMBOLS_SOURCE}，使用默认模式（持仓股票）")
        symbols = portfolio

    if not symbols:
        print("警告: 没有找到任何股票代码，将使用手动输入股票列表")
        symbols = manual if manual else ["SZSE.002842", "SZSE.002513"]

    print(f"最终订阅股票数量: {len(symbols)}")
    print(f"最终订阅列表: {', '.join(symbols)}")
    return symbols
