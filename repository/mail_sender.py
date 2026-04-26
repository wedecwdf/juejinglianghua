# repository/mail_sender.py
# -*- coding: utf-8 -*-
"""
邮件发送唯一实现
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Union
from config.mail import (
    SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL,
    SMTP_SERVER, SMTP_PORT
)

def send_email(subject: str, message: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain", "utf-8"))
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
            try:
                server.quit()
            except Exception:
                pass
        print(f"邮件发送成功: {subject}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False