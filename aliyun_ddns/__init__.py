"""
阿里云 DDNS 客户端包
"""

__version__ = "2.1.0"
__author__ = "Your Name"

# 从 core 模块导入主要功能
from .core import (
    log_message,
    valid_ip,
    get_public_ip,
    validate_config,
    load_config,
    get_dns_record,
    update_dns_record,
    create_dns_record,
    sync_records
)

# 从 gui 模块导入 GUI 应用
from .gui import DDNSTrayApp

__all__ = [
    "log_message",
    "valid_ip",
    "get_public_ip",
    "validate_config",
    "load_config",
    "get_dns_record",
    "update_dns_record",
    "create_dns_record",
    "sync_records",
    "DDNSTrayApp"
]