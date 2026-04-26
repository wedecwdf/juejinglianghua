# domain/stores/__init__.py
# 自动映射到 repository 实现，消除 domain 对 repository 的显式导入
from repository.stores import (
    SessionRegistryImpl as SessionRegistry,
    OrderLedgerImpl as OrderLedger,
    BoardStateRepositoryImpl as BoardStateRepository,
    CallbackTaskStoreImpl as CallbackTaskStore,
)

__all__ = [
    'SessionRegistry',
    'OrderLedger',
    'BoardStateRepository',
    'CallbackTaskStore',
]