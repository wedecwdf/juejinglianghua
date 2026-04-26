#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一键清除所有持久化 JSON（含 json_storage 目录）
用法：
python scripts/clear_all.py
"""
import os
import shutil

STORAGE_DIR = "json_storage"

if __name__ == "__main__":
    if os.path.isdir(STORAGE_DIR):
        try:
            shutil.rmtree(STORAGE_DIR)
            print(f"已删除整个目录: {STORAGE_DIR}")
        except Exception as e:
            print(f"删除目录失败: {e}")
    else:
        print(f"目录 {STORAGE_DIR} 不存在，无需清除")

    print("所有持久化文件已清空")