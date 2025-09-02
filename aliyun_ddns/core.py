#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云 DDNS 核心功能模块
"""

import re
import time
import yaml
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, as_completed
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
from aliyunsdkalidns.request.v20150109 import (
    DescribeDomainRecordsRequest,
    UpdateDomainRecordRequest,
    AddDomainRecordRequest
)

# 导入工具函数
from .utils import setup_logging, retry

# 配置日志
logger = logging.getLogger('aliyun_ddns')

# 全局缓存用于存储IP地址，避免频繁请求
_ip_cache = {}
_cache_timeout = 60  # 缓存60秒

def log_message(message, level=logging.INFO):
    """通用日志记录函数"""
    logger.log(level, message)

@retry(max_attempts=3, delay=1, backoff=2)
def valid_ip(ip, ipv6=False):
    """验证IP地址格式"""
    try:
        if ipv6:
            # 简化的 IPv6 验证，检查是否包含有效的十六进制字符和冒号
            # 这是一个实用的验证，而不是严格的 RFC 验证
            if not ip or not isinstance(ip, str):
                return False
            # 检查是否只包含有效的 IPv6 字符
            import re
            # 检查是否是有效的 IPv6 格式（简化版）
            if re.match(r'^[0-9a-fA-F:]+$', ip) and ':' in ip:
                # 检查是否有多个冒号
                if '::' in ip:
                    # 压缩格式，最多只能有一个 ::
                    if ip.count('::') > 1:
                        return False
                return True
            return False
        # IPv4 验证
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit() or not 0 <= int(part) <= 255:
                return False
        return True
    except Exception:
        return False

@retry(max_attempts=3, delay=1, backoff=2)
def get_public_ip(ipv6=False, services=None):
    """获取公网IP"""
    # 检查缓存
    cache_key = 'ipv6' if ipv6 else 'ipv4'
    if cache_key in _ip_cache:
        cached_time, cached_ip = _ip_cache[cache_key]
        if time.time() - cached_time < _cache_timeout:
            return cached_ip
    
    default_services = [
        'https://api.ipify.org',
        'https://ipinfo.io/ip',
        'https://ifconfig.me/ip',
        'https://icanhazip.com',
        'https://ident.me'
    ]
    
    if ipv6:
        services = services or [
            'https://api64.ipify.org',
            'https://v6.ident.me',
            'https://ipv6.icanhazip.com'
        ]
    else:
        services = services or default_services

    def fetch_ip(url):
        try:
            r = requests.get(url, timeout=10)  # 增加超时时间
            r.raise_for_status()
            ip = r.text.strip()
            return ip if valid_ip(ip, ipv6) else None
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=5) as executor:  # 增加工作线程数
        futures = [executor.submit(fetch_ip, url) for url in services]
        for future in as_completed(futures):
            ip = future.result()
            if ip:
                # 缓存结果
                _ip_cache[cache_key] = (time.time(), ip)
                return ip
    return None

def validate_config(config):
    """验证配置"""
    errors = []
    required = ['access_key_id', 'access_key_secret', 'domain', 'records']
    for field in required:
        if field not in config:
            errors.append(f"缺少配置项: {field}")
    
    if 'records' in config:
        for i, r in enumerate(config['records']):
            if 'rr' not in r:
                errors.append(f"记录{i+1}缺少rr字段")
            if 'type' not in r or r['type'] not in ['A', 'AAAA']:
                errors.append(f"记录{i+1}类型错误，必须是A或AAAA")
    
    if errors:
        raise ValueError("配置错误: " + ", ".join(errors))
    return True

def load_config(path='config.yaml'):
    """加载配置"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        # 设置默认值
        config.setdefault('interval', 300)
        config.setdefault('ttl', 600)
        
        # 为每个记录设置默认 TTL
        for record in config.get('records', []):
            record.setdefault('ttl', config['ttl'])
        
        validate_config(config)
        log_message("配置加载成功")
        return config
    except Exception as e:
        log_message(f"配置加载失败: {e}", logging.ERROR)
        raise

@retry(max_attempts=3, delay=1, backoff=2)
def get_dns_record(client, domain, rr, record_type):
    """获取DNS记录"""
    try:
        req = DescribeDomainRecordsRequest.DescribeDomainRecordsRequest()
        req.set_DomainName(domain)
        req.set_RRKeyWord(rr)
        req.set_TypeKeyWord(record_type)
        req.set_SearchMode("EXACT")
        resp = client.do_action_with_exception(req)
        records = yaml.safe_load(resp).get('DomainRecords', {}).get('Record', [])
        for r in records:
            if r.get('RR') == rr and r.get('Type') == record_type:
                return r
        return None
    except Exception as e:
        log_message(f"查询记录失败: {e}", logging.ERROR)
        return None

@retry(max_attempts=3, delay=1, backoff=2)
def update_dns_record(client, record, ip, config):
    """更新DNS记录"""
    try:
        req = UpdateDomainRecordRequest.UpdateDomainRecordRequest()
        req.set_RecordId(record['RecordId'])
        req.set_RR(record['RR'])
        req.set_Type(record['Type'])
        req.set_Value(ip)
        req.set_TTL(config.get('ttl', 600))
        client.do_action_with_exception(req)
        log_message(f"已更新记录: {record['RR']} -> {ip}")
        return True
    except Exception as e:
        log_message(f"更新记录失败: {e}", logging.ERROR)
        return False

@retry(max_attempts=3, delay=1, backoff=2)
def create_dns_record(client, domain, rr, record_type, ip, config):
    """创建DNS记录"""
    try:
        req = AddDomainRecordRequest.AddDomainRecordRequest()
        req.set_DomainName(domain)
        req.set_RR(rr)
        req.set_Type(record_type)
        req.set_Value(ip)
        req.set_TTL(config.get('ttl', 600))
        client.do_action_with_exception(req)
        log_message(f"已创建记录: {rr}.{domain} -> {ip}")
        return True
    except Exception as e:
        if "AlreadyExists" in str(e):
            log_message(f"记录已存在: {rr}.{domain}")
            return True
        log_message(f"创建记录失败: {e}", logging.ERROR)
        return False

def sync_records(config):
    """同步所有记录（带详细日志）"""
    start_time = time.time()
    try:
        client = AcsClient(
            config['access_key_id'],
            config['access_key_secret'],
            config.get('region', 'cn-hangzhou')
        )
        success_count = 0
        total_records = len(config['records'])
        log_message(f"开始同步 {total_records} 条记录")
        
        for record in config['records']:
            record_name = f"{record['rr']}.{config['domain']}"
            record_type = record['type']
            
            # 获取当前IP
            log_message(f"[{record_name}] 正在获取{record_type}地址...")
            ip = get_public_ip(record_type == 'AAAA')
            if not ip:
                log_message(f"[{record_name}] 获取IP失败", logging.ERROR)
                continue
            
            # 查询现有记录
            existing = get_dns_record(client, config['domain'], record['rr'], record_type)
            if existing:
                if existing['Value'] == ip:
                    log_message(f"[{record_name}] IP未变化: {ip}")
                    success_count += 1
                else:
                    old_ip = existing['Value']
                    if update_dns_record(client, existing, ip, config):
                        log_message(f"[{record_name}] IP已更新: {old_ip} → {ip}")
                        success_count += 1
            else:
                if create_dns_record(client, config['domain'], record['rr'], record_type, ip, config):
                    log_message(f"[{record_name}] 记录已创建: {ip}")
                    success_count += 1
        
        duration = time.time() - start_time
        log_message(f"同步完成: {success_count}/{total_records} 成功 ({duration:.1f}s)")
        return success_count > 0
    except Exception as e:
        log_message(f"同步失败: {e}", logging.ERROR)
        return False

def main():
    """主函数 - 命令行入口"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='阿里云 DDNS 客户端')
    parser.add_argument('-c', '--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细日志')
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging("logs/core.log", args.verbose)
    
    try:
        # 加载配置
        config = load_config(args.config)
        
        # 执行同步
        success = sync_records(config)
        return 0 if success else 1
    except Exception as e:
        log_message(f"程序执行失败: {e}", logging.ERROR)
        return 1

if __name__ == '__main__':
    exit(main())