# config/mail.py
# -*- coding: utf-8 -*-
# ========== 邮件配置参数 ==========
# 所有敏感信息从环境变量读取，不再硬编码
import os

SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD: str = os.getenv("SENDER_PASSWORD", "")  # 不再硬编码授权码
RECEIVER_EMAIL: str = os.getenv("RECEIVER_EMAIL", "")
SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.qq.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))

# 可在此处添加校验，避免空值导致发送失败
if not SENDER_EMAIL or not SENDER_PASSWORD:
    print("警告：邮箱配置未设置，邮件功能将不可用。请在 .env 文件中配置 SENDER_EMAIL 和 SENDER_PASSWORD")