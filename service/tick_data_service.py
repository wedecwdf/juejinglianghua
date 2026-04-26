# service/tick_data_service.py
# -*- coding: utf-8 -*-
"""
Tick数据处理服务
"""
from __future__ import annotations
from datetime import date
from typing import Dict, Any
from domain.day_data import DayData
from domain.stores import SessionRegistry
from repository.gm_data_source import load_history_data
from service.indicator_service import calculate_indicators
from config.strategy import (
    CONDITION8_RISE_PERCENT, CONDITION8_DECLINE_PERCENT,
    CONDITION8_HIGH_FREQ_RISE_PERCENT, CONDITION8_HIGH_FREQ_DECLINE_PERCENT,
    CONDITION8_LOW_FREQ_RISE_PERCENT, CONDITION8_LOW_FREQ_DECLINE_PERCENT,
    HIGH_FREQUENCY_STOCKS, LOW_FREQUENCY_STOCKS
)

def update_day_data(symbol: str, tick: Dict[str, Any], tick_date: date,
                    session_registry: SessionRegistry) -> DayData:
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
        print(f"\n===== {symbol} 新交易日开始 [{tick_date}] =====")
        print(f"{symbol} 基准价: {base_price:.4f}")
        session_registry.set(symbol, day_data)
        session_registry.reset_total_buy(symbol)
    else:
        day_data.high = max(day_data.high, tick["price"])
        day_data.low = min(day_data.low, tick["price"])
        day_data.close = tick["price"]
        day_data.volume = tick["cum_volume"]
    return day_data

def refresh_indicators(symbol: str, day_data: DayData) -> None:
    df = load_history_data(symbol, day_data.date)
    if df is not None and not df.empty:
        calculate_indicators(df, day_data)

def print_tick_snapshot(symbol: str, current_price: float, day_data: DayData) -> None:
    cond8_ref = day_data.condition8_reference_price
    if cond8_ref <= 0:
        cond8_ref = day_data.base_price
    increase = (current_price - cond8_ref) / cond8_ref
    rise_thr = CONDITION8_RISE_PERCENT
    decline_thr = CONDITION8_DECLINE_PERCENT
    if symbol in HIGH_FREQUENCY_STOCKS:
        rise_thr = CONDITION8_HIGH_FREQ_RISE_PERCENT
        decline_thr = CONDITION8_HIGH_FREQ_DECLINE_PERCENT
    elif symbol in LOW_FREQUENCY_STOCKS:
        rise_thr = CONDITION8_LOW_FREQ_RISE_PERCENT
        decline_thr = CONDITION8_LOW_FREQ_DECLINE_PERCENT
    print(f"[{symbol}] 条件8基准价={cond8_ref:.2f} 当前价={current_price:.2f} "
          f"条件8上涨阈值={rise_thr*100:.2f}% 条件8下跌阈值={decline_thr*100:.2f}% "
          f"当前涨跌幅={increase*100:+.2f}%")
    print(f"【固定基准价】{symbol} base_price={day_data.base_price:.2f}")