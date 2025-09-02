#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云 DDNS 工具函数模块
"""

import logging
import os

def setup_logging(log_file="aliyun_ddns.log", verbose=False):
    """配置日志系统"""
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else "logs"
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置日志格式
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        encoding='utf-8'  # 确保UTF-8编码，解决Windows环境下中文日志乱码问题
    )
    
    # 同时输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)
    
    return logging.getLogger('aliyun_ddns')

def is_windows():
    """检查是否为Windows系统"""
    return os.name == 'nt'

def get_config_path():
    """获取配置文件路径"""
    return "config.yaml"