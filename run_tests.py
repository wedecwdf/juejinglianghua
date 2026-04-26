#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
脱离 IDE / pytest 命令行，纯标准库跑全部单元测试
"""
import sys
import unittest
import os

# 把项目根目录加入 PYTHONPATH，解决 ModuleNotFoundError
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 自动发现 tests/unit 目录下所有 test_*.py
if __name__ == '__main__':
    start_dir = 'tests/unit'
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=start_dir, pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 退出码 0 = 全部通过，1 = 有失败
    sys.exit(0 if result.wasSuccessful() else 1)