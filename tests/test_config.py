#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置相关测试
"""

import unittest
import tempfile
import os
import yaml
from aliyun_ddns.core import load_config, validate_config

class TestConfig(unittest.TestCase):
    """配置测试类"""

    def test_default_values(self):
        """测试默认值设置"""
        config_data = """
access_key_id: test_key
access_key_secret: test_secret
domain: example.com
records:
  - rr: '@'
    type: 'A'
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_data)
            config_file = f.name

        try:
            config = load_config(config_file)
            # 检查默认值是否正确设置
            self.assertEqual(config['interval'], 300)
            self.assertEqual(config['ttl'], 600)
            # 检查记录的默认 TTL
            self.assertEqual(config['records'][0]['ttl'], 600)
        finally:
            os.unlink(config_file)

    def test_custom_values(self):
        """测试自定义值"""
        config_data = """
access_key_id: test_key
access_key_secret: test_secret
domain: example.com
records:
  - rr: '@'
    type: 'A'
interval: 600
ttl: 1200
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_data)
            config_file = f.name

        try:
            config = load_config(config_file)
            # 检查自定义值是否正确设置
            self.assertEqual(config['interval'], 600)
            self.assertEqual(config['ttl'], 1200)
        finally:
            os.unlink(config_file)

    def test_record_validation(self):
        """测试记录验证"""
        # 有效的记录配置
        valid_records = [
            {"rr": "@", "type": "A"},
            {"rr": "www", "type": "AAAA"},
            {"rr": "mail", "type": "A"}
        ]
        
        config = {
            "access_key_id": "test_key",
            "access_key_secret": "test_secret",
            "domain": "example.com",
            "records": valid_records
        }
        
        self.assertTrue(validate_config(config))

        # 无效的记录配置
        invalid_records = [
            {"rr": "@"},  # 缺少 type
            {"type": "A"},  # 缺少 rr
            {"rr": "@", "type": "INVALID"}  # 无效的类型
        ]
        
        for i, record in enumerate(invalid_records):
            with self.subTest(record=record):
                config["records"] = [record]
                with self.assertRaises(ValueError):
                    validate_config(config)

if __name__ == '__main__':
    unittest.main()