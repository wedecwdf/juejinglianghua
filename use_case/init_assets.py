# use_case/init_assets.py
# -*- coding: utf-8 -*-
"""
资产合并：持仓 + 手动，返回最终订阅列表
使用配置对象获取股票来源参数。
"""
from __future__ import annotations
import logging
from typing import List
from config.account import ACCOUNT_ID
from config.strategy.config_objects import StrategyConfig, load_strategy_config

logger = logging.getLogger(__name__)

def build_tracking_symbols() -> List[str]:
    from adapter.gm_adapter import fetch_positions
    config = load_strategy_config()
    portfolio = []
    if ACCOUNT_ID:
        try:
            positions = fetch_positions()
            portfolio = [pos["symbol"] for pos in positions
                         if pos["volume"] > 0 and pos["side"] == 1]
            for sym in portfolio:
                vol = next(p['volume'] for p in positions if p['symbol'] == sym)
                logger.info("发现持仓股票: %s, 数量: %d", sym, vol)
        except Exception as e:
            logger.exception("获取账户持仓失败")

    manual = []
    if config.entry.manual_symbols_enabled and config.entry.manual_symbols:
        manual = list({s.strip() for s in config.entry.manual_symbols if s.strip()})
        logger.info("手动输入股票代码: %s", ', '.join(manual))

    if config.entry.stock_source == "position":
        symbols = portfolio
        logger.info("股票代码来源: 仅持仓股票")
    elif config.entry.stock_source == "manual":
        symbols = manual
        logger.info("股票代码来源: 仅手动输入")
    elif config.entry.stock_source == "both":
        symbols = list(set(portfolio + manual))
        logger.info("股票代码来源: 持仓股票 + 手动输入")
    else:
        logger.warning("未知的股票代码来源模式: %s，使用默认模式（持仓股票）", config.entry.stock_source)
        symbols = portfolio

    if not symbols:
        logger.warning("警告: 没有找到任何股票代码，将使用手动输入股票列表")
        symbols = manual if manual else ["SZSE.002842", "SZSE.002513"]

    logger.info("最终订阅股票数量: %d", len(symbols))
    logger.info("最终订阅列表: %s", ', '.join(symbols))
    return symbols