# domain/constants.py
# -*- coding: utf-8 -*-
from enum import Enum

class ConditionType(str, Enum):
    CONDITION2 = "condition2"
    CONDITION4 = "condition4"
    CONDITION5 = "condition5"
    CONDITION6 = "condition6"
    CONDITION7 = "condition7"
    CONDITION8 = "condition8"
    CONDITION9 = "condition9"
    PYRAMID_BUY = "pyramid_buy"
    BOARD_BREAK_STATIC = "board_break_static"
    BOARD_BREAK_DYNAMIC = "board_break_dynamic"
    BOARD_DYNAMIC_PROFIT = "board_dynamic_profit"
    DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT = "dynamic_profit_next_day_adjustment"
    CONDITION8_PYRAMID_PROFIT = "condition8_pyramid_profit"

class OrderSide(str, Enum):
    BUY = "买入"
    SELL = "卖出"

class StockBoard(str, Enum):
    MAIN = "MAIN"
    GEM = "GEM"
    ST = "ST"
    BSE = "BSE"