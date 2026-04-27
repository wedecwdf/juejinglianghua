# service/indicator_service.py
# -*- coding: utf-8 -*-
"""
指标计算，无外部依赖
"""
from __future__ import annotations
import logging
import numpy as np
import talib as ta
import pandas as pd
from typing import Any, Dict, Optional
from config.strategy import (
    MA_PERIODS, CCI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL, MACD_MIN_PERIOD,
    CCI_UPPER_LIMIT, CCI_LOWER_LIMIT, VOLUME_BAR_COUNT, MACD_HIST_BAR_COUNT
)
from domain.day_data import DayData

logger = logging.getLogger(__name__)

def calculate_indicators(df: pd.DataFrame, day_data: DayData) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    close_prices = df["close"].values.astype(float)

    for period in MA_PERIODS:
        if len(close_prices) >= period:
            ma_val = ta.SMA(close_prices, timeperiod=period)[-1]
            if not np.isnan(ma_val):
                results[f"MA{period}"] = float(ma_val)
                if period == 4:
                    day_data.ma4 = float(ma_val)
                elif period == 8:
                    day_data.ma8 = float(ma_val)
                elif period == 12:
                    day_data.ma12 = float(ma_val)
            else:
                results[f"MA{period}"] = None

    high_prices = df["high"].values.astype(float)
    low_prices = df["low"].values.astype(float)

    if len(close_prices) >= CCI_PERIOD:
        tp = (high_prices + low_prices + close_prices) / 3.0
        ma_tp = ta.SMA(tp, timeperiod=CCI_PERIOD)
        mad = np.zeros_like(tp)
        for i in range(CCI_PERIOD - 1, len(tp)):
            window = tp[i - CCI_PERIOD + 1:i + 1]
            mad[i] = np.mean(np.abs(window - ma_tp[i]))
        cci_values = np.where(mad != 0, (tp - ma_tp) / (0.015 * mad), 0)
        cci_val = float(cci_values[-1])
        results["CCI"] = cci_val
        day_data.cci = cci_val
    else:
        results["CCI"] = None

    if len(close_prices) >= MACD_MIN_PERIOD:
        macd, macd_signal, macd_hist = ta.MACD(
            close_prices,
            fastperiod=MACD_FAST,
            slowperiod=MACD_SLOW,
            signalperiod=MACD_SIGNAL
        )
        macd_hist_all = macd_hist * 2
        results["MACD_hist"] = float(macd_hist_all[-1]) if not np.isnan(macd_hist_all[-1]) else None
    else:
        results["MACD_hist"] = None

    return results