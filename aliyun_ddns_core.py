import re
import time
import yaml
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
from aliyunsdkalidns.request.v20150109 import (
    DescribeDomainRecordsRequest,
    UpdateDomainRecordRequest,
    AddDomainRecordRequest
)

logger = logging.getLogger('aliyun_ddns')

def log_message(message, level=logging.INFO):
    """通用日志记录函数"""
    logger.log(level, message)

def valid_ip(ip, ipv6=False):
    """验证IP地址格式"""
    try:
        if ipv6:
            return bool(re.match(r"^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$", ip, re.I))
        return bool(re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip))
    except Exception:
        return False

def get_public_ip(ipv6=False, services=None):
    """获取公网IP"""
    default_services = [
        'https://api.ipify.org',
        'https://ipinfo.io/ip',
        'https://ifconfig.me/ip'
    ]
    if ipv6:
        services = [
            'https://api64.ipify.org',
            'https://v6.ident.me'
        ]
    else:
        services = default_services

    def fetch_ip(url):
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            ip = r.text.strip()
            return ip if valid_ip(ip, ipv6) else None
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(fetch_ip, url) for url in services]
        for future in as_completed(futures):
            ip = future.result()
            if ip:
                return ip
    return None

def validate_config(config):
    """验证配置"""
    errors = []
    required = ['access_key_id', 'access_key_secret', 'domain', 'records']
    for field in required:
        if field not in config:
            errors.append(f"缺少{field}")
    if 'records' in config:
        for i, r in enumerate(config['records']):
            if 'rr' not in r:
                errors.append(f"记录{i+1}缺少rr")
            if 'type' not in r or r['type'] not in ['A', 'AAAA']:
                errors.append(f"记录{i+1}类型错误")
    if errors:
        raise ValueError("配置错误: " + ", ".join(errors))
    return True

def load_config(path='config.yaml'):
    """加载配置"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        config.setdefault('interval', 300)
        for record in config.get('records', []):
            record.setdefault('ttl', 600)
        validate_config(config)
        log_message("配置加载成功")
        return config
    except Exception as e:
        log_message("配置加载失败", logging.ERROR)
        raise

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
        log_message(f"已更新: {record['RR']} -> {ip}")
        return True
    except Exception as e:
        log_message(f"更新失败: {e}", logging.ERROR)
        return False

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
        log_message(f"已创建: {rr}.{domain} -> {ip}")
        return True
    except Exception as e:
        if "AlreadyExists" in str(e):
            return True
        log_message(f"创建失败: {e}", logging.ERROR)
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
                    if update_dns_record(client, existing, ip, record):
                        log_message(f"[{record_name}] IP已更新: {old_ip} → {ip}")
                        success_count += 1
            else:
                if create_dns_record(client, config['domain'], record['rr'], record_type, ip, record):
                    log_message(f"[{record_name}] 记录已创建: {ip}")
                    success_count += 1
        duration = time.time() - start_time
        log_message(f"同步完成: {success_count}/{total_records} 成功 ({duration:.1f}s)")
        return success_count > 0
    except Exception as e:
        log_message(f"同步失败: {e}", logging.ERROR)
        return False
