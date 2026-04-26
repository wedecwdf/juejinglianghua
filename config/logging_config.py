#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全局日志配置 - 方案A：全局捕获，不改旧代码
功能：
1. 重定向 sys.stdout/sys.stderr 到 logging，自动捕获所有 print()
2. 同时输出到控制台和文件（按天轮转，保留30天）
3. 线程安全，支持量化交易的高频并发
4. 单例模式：防止重复初始化（多次调用无害）
"""
import sys
import logging
import threading
from datetime import datetime
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

# 模块级单例标志（防止重复初始化）
_is_logging_configured = False
_lock = threading.Lock()

# 日志目录（与 scripts/export_log.py 保持一致）
LOG_DIR = Path("log")
LOG_DIR.mkdir(exist_ok=True)

# 格式：时间 - 级别 - 线程名 - 消息
LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class StreamToLogger:
    """
    文件类对象，将 write() 调用转译为 logging 调用。
    用于无缝接管 sys.stdout/stderr，使所有 print() 带时间戳入库。
    """

    def __init__(self, logger, level=logging.INFO):
        self.logger = logger
        self.level = level
        self.buffer = ""
        self.lock = threading.Lock()

    def write(self, buf):
        # 行缓冲处理：确保每行独立日志带时间戳
        with self.lock:
            self.buffer += buf
            lines = self.buffer.split('\n')
            # 保留最后一行（可能未换行）
            self.buffer = lines[-1]
            # 提交完整行到日志
            for line in lines[:-1]:
                if line.strip():
                    self.logger.log(self.level, line.strip())

    def flush(self):
        with self.lock:
            if self.buffer.strip():
                self.logger.log(self.level, self.buffer.strip())
                self.buffer = ""

    def isatty(self):
        return False  # 非TTY，避免部分库（如colorama）的冲突


def setup_global_logging():
    """
    初始化全局日志捕获。
    必须在程序最早入口调用（如 main.py 的 print_startup_info() 开头）。
    重复调用将直接返回，不做任何操作（幂等性）。
    """
    global _is_logging_configured

    with _lock:
        if _is_logging_configured:
            # 已初始化，直接返回，不做任何操作
            return logging.getLogger()

        # 配置 Root Logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # 清理已有 Handler（防御性，理论上不应有）
        if root_logger.handlers:
            for h in root_logger.handlers[:]:
                root_logger.removeHandler(h)

        # 1. 控制台 Handler（使用原始 sys.__stdout__，避免循环）
        console_handler = logging.StreamHandler(sys.__stdout__)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # 2. 文件 Handler（按天轮转，午夜自动切割，保留30天）
        log_file = LOG_DIR / f"strategy_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8',
            delay=False
        )
        # 确保文件名包含日期（suffix 会在轮转时自动追加日期）
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # 3. 接管标准输出/错误（仅当尚未接管时）
        if not isinstance(sys.stdout, StreamToLogger):
            stdout_logger = logging.getLogger("STDOUT")
            sys.stdout = StreamToLogger(stdout_logger, logging.INFO)

        if not isinstance(sys.stderr, StreamToLogger):
            stderr_logger = logging.getLogger("STDERR")
            sys.stderr = StreamToLogger(stderr_logger, logging.ERROR)

        # 记录启动标记（仅第一次）
        root_logger.info("=" * 80)
        root_logger.info("日志系统初始化完成 | 全局捕获模式（方案A）")
        root_logger.info(f"日志文件路径: {log_file.absolute()}")
        root_logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        root_logger.info("所有 print() 输出将同时记录到控制台和上述文件")
        root_logger.info("=" * 80)

        _is_logging_configured = True
        return root_logger


def restore_stdio():
    """恢复标准输出（程序退出时调用，防止资源泄露）"""
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__