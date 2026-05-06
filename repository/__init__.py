# repository/__init__.py
"""
持久化层，仅暴露邮件发送和文件持久化工具。
不再包含 StateGateway 单例（已彻底移除）。
"""

from .mail_sender import send_email
from .persistence.file_persistence import FilePersistence

__all__ = ['send_email', 'FilePersistence']