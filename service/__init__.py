# service/__init__.py
# -*- coding: utf-8 -*-
"""
纯业务逻辑，不依赖 GM Context
"""
from .indicator_service import calculate_indicators
from .pyramid_service import (
    add_callback_task,
    remove_callback_task,
    get_callback_task,
    check_callback_strategy,
    complete_callback_task,
    should_create_callback_task,
)
from .board_service import (
    handle_board_counting,
    handle_board_break_mechanism,
    handle_dynamic_profit_on_board_break
)
from .day_adjust_service import (
    set_config as set_day_adjust_config,
    check_dynamic_profit_next_day_adjustment,
    initialize_next_day_adjustment,
    update_dynamic_profit_high_lines,
    disable_next_day_adjustment_if_dynamic_profit_triggered
)
from .condition_service import (
    check_condition2,
    check_condition4,
    check_condition5,
    check_condition6,
    check_condition7,
    check_condition8,
    check_condition9,
)
from .order_executor import place_sell, place_buy, sell_qty_by_percent
from .tick_data_service import update_day_data, refresh_indicators, print_tick_snapshot