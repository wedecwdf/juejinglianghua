# repository/__init__.py
"""
持久化层，仅暴露 StateGateway 和邮件发送。
不再包含 gm_data_source（已迁移到 adapter）。
"""
from .state_gateway import StateGateway
from .mail_sender import send_email