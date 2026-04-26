# service/tick_data_service.py
# -*- coding: utf-8 -*-
"""
Tick数据处理服务
修改：print_tick_snapshot 可接受 session_registry 来获取条件8参考价及阈值。
"""
from __future__ import annotations
from datetime import date
from typing import Dict, Any, Optional
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
    """更新或创建 DayData（纯行情），不涉及条件状态"""
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

def print_tick_snapshot(symbol: str, current_price: float, day_data: DayData,
                        session_registry: Optional[SessionRegistry] = None) -> None:
    # 获取条件8参考价（上下文中）
    cond8_ref = day_data.base_price
    if session_registry:
        ctx8 = session_registry.get_condition8(symbol, day_data.base_price)
        ref = ctx8.condition8_reference_price
        if ref and ref > 0:
            cond8_ref = ref
    increase = (current_price - cond8_ref) / cond8_ref if cond8_ref > 0 else 0

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