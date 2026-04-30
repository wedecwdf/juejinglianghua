# adapter/__init__.py
"""
与 GM 事件直接对接的薄层。
仅导出上下文包装器，避免循环导入。
"""
from .context_wrapper import ContextWrapper