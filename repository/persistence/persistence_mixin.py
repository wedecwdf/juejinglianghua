# repository/persistence/persistence_mixin.py
# -*- coding: utf-8 -*-
"""
状态持久化 Mixin：负责所有 JSON 文件的读写
修改：所有保存函数在打开文件前确保目录存在。
"""
from __future__ import annotations
import json
import os
from datetime import datetime, date
from typing import TYPE_CHECKING

from repository.core.serializer import _json_default, _slots_to_dict, _dict_to_slots
from repository.core.file_path import (
    STATE_FILE,
    PYRAMID_BASE_PRICE_FILE,
    DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_FILE,
    PENDING_ORDERS_FILE,
    CONDITION_TRIGGERS_FILE,
    BOARD_COUNT_FILE,
)

from domain.day_data import DayData
from domain.board import BoardStatus, BoardBreakStatus, BoardCountData

if TYPE_CHECKING:
    from repository.core.state_gateway_impl import _StateGatewayImpl

class _PersistenceMixin:
    """
    提供状态加载、保存、清档能力
    包含动态回调加仓任务的持久化
    """

    def save_all(self: "_StateGatewayImpl") -> bool:
        try:
            self._save_strategy_state()
            self._save_callback_addition_tasks()
            self._save_dynamic_profit_adjustment()
            self._save_pending_orders()
            self._save_condition_triggers()
            self._save_board_count()
            return True
        except Exception as e:
            print(f"保存状态失败: {e}")
            return False

    def clear_all(self: "_StateGatewayImpl") -> bool:
        try:
            files = [
                STATE_FILE,
                PYRAMID_BASE_PRICE_FILE,
                DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_FILE,
                PENDING_ORDERS_FILE,
                CONDITION_TRIGGERS_FILE,
                BOARD_COUNT_FILE,
            ]
            for fp in files:
                if os.path.exists(fp):
                    os.remove(fp)
                    print(f"已清除 {fp}")
            self._init()
            return True
        except Exception as e:
            print(f"清除状态文件失败: {e}")
            return False

    def _load_all(self: "_StateGatewayImpl") -> None:
        self._load_strategy_state()
        self._load_callback_addition_tasks()
        self._load_dynamic_profit_adjustment()
        self._load_pending_orders()
        self._load_condition_triggers()
        self._load_board_count()

    # ========== 策略状态 ==========
    def _load_strategy_state(self: "_StateGatewayImpl") -> None:
        if not os.path.exists(STATE_FILE):
            return
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            raw = loaded.get("current_day_data", {})
            for sym, dat in raw.items():
                if "date" in dat and dat["date"]:
                    try:
                        dat["date"] = datetime.strptime(dat["date"], "%Y-%m-%d").date()
                    except Exception:
                        pass
                adj = dat.get("dynamic_profit_next_day_adjustment")
                if adj and "stop_loss_price" in adj:
                    adj["stop_loss_price"] = float(adj["stop_loss_price"])
                self.current_day_data[sym] = DayData.from_dict(sym, dat)
            for sym, d in loaded.get("board_status", {}).items():
                self.board_status[sym] = _dict_to_slots(BoardStatus, d)
            for sym, d in loaded.get("board_break_status", {}).items():
                self.board_break_status[sym] = _dict_to_slots(BoardBreakStatus, d)
            tbq = loaded.get("total_buy_quantity", {})
            if isinstance(tbq, dict):
                self.total_buy_quantity = tbq
            print(f"从 {STATE_FILE} 加载策略状态成功")
        except Exception as e:
            print(f"加载策略状态失败: {e}")

    def _save_strategy_state(self: "_StateGatewayImpl") -> None:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        state_to_save = {
            "current_day_data": {},
            "total_buy_quantity": self.total_buy_quantity.copy(),
            "board_status": {},
            "board_break_status": {},
        }
        for sym, day_data_obj in self.current_day_data.items():
            data_copy = day_data_obj.to_dict()
            if "date" in data_copy and isinstance(data_copy["date"], date):
                data_copy["date"] = data_copy["date"].isoformat()
            state_to_save["current_day_data"][sym] = data_copy
        for sym, obj in self.board_status.items():
            state_to_save["board_status"][sym] = _slots_to_dict(obj)
        for sym, obj in self.board_break_status.items():
            state_to_save["board_break_status"][sym] = _slots_to_dict(obj)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_to_save, f, ensure_ascii=False, indent=4, default=_json_default)

    # ========== 动态回调加仓任务 ==========
    def _load_callback_addition_tasks(self: "_StateGatewayImpl") -> None:
        if not os.path.exists(PYRAMID_BASE_PRICE_FILE):
            return
        try:
            with open(PYRAMID_BASE_PRICE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "callback_addition_tasks" in data:
                self.callback_addition_tasks = data["callback_addition_tasks"]
                print(f"从 {PYRAMID_BASE_PRICE_FILE} 加载动态回调加仓任务成功")
            else:
                self.callback_addition_tasks = {}
                print(f"检测到旧版金字塔数据格式，已清空并准备使用新格式")
        except Exception as e:
            print(f"加载动态回调加仓任务失败: {e}")
            self.callback_addition_tasks = {}

    def _save_callback_addition_tasks(self: "_StateGatewayImpl") -> None:
        os.makedirs(os.path.dirname(PYRAMID_BASE_PRICE_FILE), exist_ok=True)
        try:
            data_to_save = {
                "callback_addition_tasks": self.callback_addition_tasks,
                "_comment": "动态回调加仓任务（替代原金字塔加仓）",
                "_updated_at": datetime.now().isoformat()
            }
            with open(PYRAMID_BASE_PRICE_FILE, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4, default=_json_default)
        except Exception as e:
            print(f"保存动态回调加仓任务失败: {e}")

    # ========== 动态止盈次日调整 ==========
    def _load_dynamic_profit_adjustment(self: "_StateGatewayImpl") -> None:
        if not os.path.exists(DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_FILE):
            return
        try:
            with open(DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_FILE, "r", encoding="utf-8") as f:
                adj_data = json.load(f)
            for sym, info in adj_data.items():
                if "timestamp" in info and info["timestamp"]:
                    try:
                        info["timestamp"] = datetime.fromisoformat(info["timestamp"])
                    except Exception:
                        pass
            self.dynamic_profit_next_day_adjustment_data = adj_data
            print(f"从 {DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_FILE} 加载动态止盈次日调整机制数据成功")
        except Exception as e:
            print(f"加载动态止盈次日调整机制数据失败: {e}")

    def _save_dynamic_profit_adjustment(self: "_StateGatewayImpl") -> None:
        os.makedirs(os.path.dirname(DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_FILE), exist_ok=True)
        adj_data_to_save = {}
        for sym, info in self.dynamic_profit_next_day_adjustment_data.items():
            info_copy = info.copy()
            if "timestamp" in info_copy and isinstance(info_copy["timestamp"], datetime):
                info_copy["timestamp"] = info_copy["timestamp"].isoformat()
            adj_data_to_save[sym] = info_copy
        with open(DYNAMIC_PROFIT_NEXT_DAY_ADJUSTMENT_FILE, "w", encoding="utf-8") as f:
            json.dump(adj_data_to_save, f, ensure_ascii=False, indent=4, default=_json_default)

    # ========== 挂单 ==========
    def _load_pending_orders(self: "_StateGatewayImpl") -> None:
        if not os.path.exists(PENDING_ORDERS_FILE):
            return
        try:
            with open(PENDING_ORDERS_FILE, "r", encoding="utf-8") as f:
                self.pending_orders = json.load(f)
            print(f"从 {PENDING_ORDERS_FILE} 加载待处理订单成功")
        except Exception as e:
            print(f"加载待处理订单失败: {e}")

    def _save_pending_orders(self: "_StateGatewayImpl") -> None:
        os.makedirs(os.path.dirname(PENDING_ORDERS_FILE), exist_ok=True)
        with open(PENDING_ORDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.pending_orders, f, ensure_ascii=False, indent=4, default=_json_default)

    # ========== 条件触发记录 ==========
    def _load_condition_triggers(self: "_StateGatewayImpl") -> None:
        if not os.path.exists(CONDITION_TRIGGERS_FILE):
            return
        try:
            with open(CONDITION_TRIGGERS_FILE, "r", encoding="utf-8") as f:
                self.condition_triggers = json.load(f)
            print(f"从 {CONDITION_TRIGGERS_FILE} 加载条件触发记录成功")
        except Exception as e:
            print(f"加载条件触发记录失败: {e}")

    def _save_condition_triggers(self: "_StateGatewayImpl") -> None:
        os.makedirs(os.path.dirname(CONDITION_TRIGGERS_FILE), exist_ok=True)
        with open(CONDITION_TRIGGERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.condition_triggers, f, ensure_ascii=False, indent=4, default=_json_default)

    # ========== 板数 ==========
    def _load_board_count(self: "_StateGatewayImpl") -> None:
        if not os.path.exists(BOARD_COUNT_FILE):
            return
        try:
            with open(BOARD_COUNT_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for sym, d in raw.get("board_count_data", {}).items():
                bcd = _dict_to_slots(BoardCountData, d)
                self.board_count_data[sym] = bcd
            print(f"从 {BOARD_COUNT_FILE} 加载板数数据成功")
        except Exception as e:
            print(f"加载板数数据失败: {e}")

    def _save_board_count(self: "_StateGatewayImpl") -> None:
        os.makedirs(os.path.dirname(BOARD_COUNT_FILE), exist_ok=True)
        try:
            data_to_save = {}
            for sym, obj in self.board_count_data.items():
                data_to_save[sym] = _slots_to_dict(obj)
            with open(BOARD_COUNT_FILE, "w", encoding="utf-8") as f:
                json.dump({"board_count_data": data_to_save}, f, ensure_ascii=False, indent=4, default=_json_default)
        except Exception as e:
            print(f"保存板数数据失败: {e}")