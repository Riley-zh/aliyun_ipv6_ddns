#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心功能模块测试
"""

import unittest
import tempfile
import os
from aliyun_ddns.core import (
    valid_ip,
    validate_config,
    load_config
)

class TestCoreFunctions(unittest.TestCase):
    """核心功能测试类"""

    def test_valid_ip_ipv4(self):
        """测试 IPv4 地址验证"""
        self.assertTrue(valid_ip("192.168.1.1"))
        self.assertTrue(valid_ip("8.8.8.8"))
        self.assertFalse(valid_ip("256.1.1.1"))
        self.assertFalse(valid_ip("192.168.1"))
        self.assertFalse(valid_ip("invalid.ip"))

    def test_valid_ip_ipv6(self):
        """测试 IPv6 地址验证"""
        self.assertTrue(valid_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334", ipv6=True))
        self.assertTrue(valid_ip("2001:db8:85a3::8a2e:370:7334", ipv6=True))
        self.assertFalse(valid_ip("invalid:ipv6", ipv6=True))

    def test_validate_config_valid(self):
        """测试有效配置验证"""
        valid_config = {
            "access_key_id": "test_key",
            "access_key_secret": "test_secret",
            "domain": "example.com",
            "records": [
                {"rr": "@", "type": "A"},
                {"rr": "www", "type": "AAAA"}
            ]
        }
        self.assertTrue(validate_config(valid_config))

    def test_validate_config_missing_fields(self):
        """测试缺少必要字段的配置验证"""
        invalid_config = {
            "access_key_id": "test_key",
            # 缺少 access_key_secret, domain, records
        }
        with self.assertRaises(ValueError) as context:
            validate_config(invalid_config)
        self.assertIn("缺少配置项", str(context.exception))

    def test_validate_config_invalid_record_type(self):
        """测试无效记录类型的配置验证"""
        invalid_config = {
            "access_key_id": "test_key",
            "access_key_secret": "test_secret",
            "domain": "example.com",
            "records": [
                {"rr": "@", "type": "INVALID"}
            ]
        }
        with self.assertRaises(ValueError) as context:
            validate_config(invalid_config)
        self.assertIn("类型错误", str(context.exception))

    def test_load_config_valid(self):
        """测试加载有效配置文件"""
        config_data = """
access_key_id: test_key
access_key_secret: test_secret
domain: example.com
records:
  - rr: '@'
    type: 'A'
interval: 300
ttl: 600
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_data)
            config_file = f.name

        try:
            config = load_config(config_file)
            self.assertEqual(config['access_key_id'], 'test_key')
            self.assertEqual(config['domain'], 'example.com')
            self.assertEqual(config['interval'], 300)
            self.assertEqual(config['ttl'], 600)
        finally:
            os.unlink(config_file)

    def test_load_config_invalid(self):
        """测试加载无效配置文件"""
        config_data = """
# 无效的配置文件，缺少必要字段
invalid_field: value
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_data)
            config_file = f.name

        try:
            with self.assertRaises(ValueError):
                load_config(config_file)
        finally:
            os.unlink(config_file)

if __name__ == '__main__':
    unittest.main()