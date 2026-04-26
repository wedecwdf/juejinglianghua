# scripts/export_log.py
# -*- coding: utf-8 -*-
"""
打包并邮件发送当日日志
"""
import os
import zipfile
from datetime import datetime
from repository.mail_sender import send_email

LOG_DIR = "log"

def export_log() -> None:
    date_str = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(LOG_DIR, f"strategy_{date_str}.log")
    if not os.path.exists(log_file):
        print(f"日志文件不存在: {log_file}")
        return
    zip_path = os.path.join(LOG_DIR, f"strategy_{date_str}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(log_file, os.path.basename(log_file))
    with open(zip_path, "rb") as f:
        content = f.read()
    subject = f"策略日志 {date_str}"
    body = f"{date_str} 策略运行日志见附件"
    # 发送带附件邮件（简化版：直接 base64 字符串）
    import base64
    attachment = base64.b64encode(content).decode()
    send_email(subject, f"{body}\n\n附件：{attachment}")
    print(f"已发送日志邮件: {zip_path}")

if __name__ == "__main__":
    export_log()