# -*- coding: utf-8 -*-
import os
from pathlib import Path
from dotenv import load_dotenv

# 载入 .env 文件（与项目根目录平级即可）
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# ========== 账户ID配置 ==========
ACCOUNT_ID: str = os.getenv("ACCOUNT_ID", "")

# ========== 账户数据导出配置 ==========
ACCOUNT_DATA_EXPORT_ENABLED: bool = (
    os.getenv("ACCOUNT_DATA_EXPORT_ENABLED", "true").lower() == "true"
)
ACCOUNT_DATA_EXPORT_INTERVAL: int = int(
    os.getenv("ACCOUNT_DATA_EXPORT_INTERVAL", "5")
)
ACCOUNT_DATA_EXPORT_DIR: str = os.getenv(
    "ACCOUNT_DATA_EXPORT_DIR", "account_data"
)