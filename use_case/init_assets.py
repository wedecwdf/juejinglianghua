# use_case/init_assets.py
# -*- coding: utf-8 -*-
"""
资产合并：持仓 + 手动，返回最终订阅列表
"""
from __future__ import annotations
import logging
from typing import List
from config.account import ACCOUNT_ID
from config.strategy import (
    SYMBOLS_SOURCE,
    MANUAL_SYMBOLS_ENABLED,
    MANUAL_SYMBOLS
)

logger = logging.getLogger(__name__)

def get_portfolio_symbols() -> List[str]:
    if not ACCOUNT_ID:
        logger.error("错误: 未配置账户ID")
        return []
    try:
        from gm.api import get_position as gm_get_position
        positions = gm_get_position()
        symbols = [pos["symbol"] for pos in positions
                   if pos["volume"] > 0 and pos["side"] == 1]
        for sym in symbols:
            vol = next(p['volume'] for p in positions if p['symbol'] == sym)
            logger.info("发现持仓股票: %s, 数量: %d", sym, vol)
        return symbols
    except Exception as e:
        logger.exception("获取账户持仓失败")
        return []

def get_manual_symbols() -> List[str]:
    if not MANUAL_SYMBOLS_ENABLED or not MANUAL_SYMBOLS:
        logger.info("手动输入股票代码功能未启用或列表为空")
        return []
    valid = list({s.strip() for s in MANUAL_SYMBOLS if s.strip()})
    logger.info("手动输入股票代码: %s", ', '.join(valid))
    return valid

def build_tracking_symbols() -> List[str]:
    portfolio = get_portfolio_symbols()
    manual = get_manual_symbols()
    if SYMBOLS_SOURCE == "position":
        symbols = portfolio
        logger.info("股票代码来源: 仅持仓股票")
    elif SYMBOLS_SOURCE == "manual":
        symbols = manual
        logger.info("股票代码来源: 仅手动输入")
    elif SYMBOLS_SOURCE == "both":
        symbols = list(set(portfolio + manual))
        logger.info("股票代码来源: 持仓股票 + 手动输入")
    else:
        logger.warning("未知的股票代码来源模式: %s，使用默认模式（持仓股票）", SYMBOLS_SOURCE)
        symbols = portfolio

    if not symbols:
        logger.warning("警告: 没有找到任何股票代码，将使用手动输入股票列表")
        symbols = manual if manual else ["SZSE.002842", "SZSE.002513"]

    logger.info("最终订阅股票数量: %d", len(symbols))
    logger.info("最终订阅列表: %s", ', '.join(symbols))
    return symbols