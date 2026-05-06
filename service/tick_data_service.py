# service/tick_data_service.py
# -*- coding: utf-8 -*-
"""
Tick数据处理服务，阈值显示和指标刷新均通过传入的配置对象进行。
"""

from __future__ import annotations
import logging
from datetime import date
from typing import Dict, Any

from domain.day_data import DayData
from domain.stores import SessionRegistry
from domain.stores.context_store import ContextStore
from service.indicator_service import calculate_indicators
from config.strategy.config_objects import Condition8Config, TechIndicatorConfig

logger = logging.getLogger(__name__)


def update_day_data(symbol: str, tick: Dict[str, Any], tick_date: date,
                    session_registry: SessionRegistry) -> DayData:
    """更新当日行情数据，如果是新交易日则创建 DayData"""
    day_data = session_registry.get(symbol)
    if day_data is None or not day_data.initialized or day_data.date != tick_date:
        base_price = tick["price"]
        day_data = DayData(symbol, base_price, tick_date)
        day_data.initialized = True
        day_data.open = tick["price"]
        day_data.high = tick["price"]
        day_data.low = tick["price"]
        day_data.close = tick["price"]
        day_data.volume = tick["cum_volume"]
        logger.info("===== %s 新交易日开始 [%s] =====", symbol, tick_date)
        logger.info("%s 基准价: %.4f", symbol, base_price)
        session_registry.set(symbol, day_data)
        session_registry.reset_total_buy(symbol)
    else:
        day_data.high = max(day_data.high, tick["price"])
        day_data.low = min(day_data.low, tick["price"])
        day_data.close = tick["price"]
        day_data.volume = tick["cum_volume"]
    return day_data


def refresh_indicators(symbol: str, day_data: DayData,
                       tech_config: TechIndicatorConfig) -> None:
    """重新加载历史数据并计算技术指标"""
    from adapter.gm_adapter import load_history_data
    df = load_history_data(symbol, day_data.date, tech_config.max_history_days)
    if df is not None and not df.empty:
        calculate_indicators(df, day_data, tech_config)


def print_tick_snapshot(symbol: str, current_price: float, day_data: DayData,
                        session_registry: SessionRegistry,
                        context_store: ContextStore,
                        condition8_config: Condition8Config) -> None:
    """打印当前 tick 快照日志，包含条件8相关阈值信息"""
    cond8_ref = day_data.base_price
    try:
        ctx8 = context_store.get('condition8', symbol)
        ref = ctx8.condition8_reference_price
        if ref and ref > 0:
            cond8_ref = ref
    except KeyError:
        pass

    increase = (current_price - cond8_ref) / cond8_ref if cond8_ref > 0 else 0
    from service.conditions.utils import _get_condition8_thresholds
    rise_thr, decline_thr = _get_condition8_thresholds(symbol, condition8_config)

    logger.info(
        "[%s] 条件8基准价=%.2f 当前价=%.2f 条件8上涨阈值=%.2f%% 条件8下跌阈值=%.2f%% 当前涨跌幅=%+.2f%%",
        symbol, cond8_ref, current_price, rise_thr * 100, decline_thr * 100, increase * 100
    )
    logger.info("【固定基准价】%s base_price=%.2f", symbol, day_data.base_price)