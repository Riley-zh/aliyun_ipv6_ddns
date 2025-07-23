import os
import sys
import time
import yaml
import logging
import threading
import subprocess
import platform
import pystray
from PIL import Image, ImageDraw
from tkinter import Tk, messagebox
import aliyun_ddns_core as core

APP_NAME = "阿里云DDNS"
VERSION = "2.1"
CONFIG_FILE = "config.yaml"

# 简化日志
logging.basicConfig(
    filename="aliyun_ddns.log",
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%m-%d %H:%M'
)
logger = logging.getLogger()

def log_message(message, level=logging.INFO):
    """通用日志记录函数"""
    logger.log(level, message)

class DDNSTrayApp:
    def __init__(self):
        self.running = True
        self.config = None
        self.config_mtime = 0
        # 立即加载配置
        self._load_config()
        # 创建托盘
        self.icon = pystray.Icon(
            APP_NAME,
            self._create_icon(),
            APP_NAME,
            self._create_menu()
        )
        log_message("应用已启动")

    def _load_config(self):
        """加载配置"""
        try:
            if not os.path.exists(CONFIG_FILE):
                self._create_default_config()
            self.config_mtime = os.path.getmtime(CONFIG_FILE)
            self.config = core.load_config(CONFIG_FILE)
        except Exception as e:
            log_message(f"配置错误: {e}", logging.ERROR)
            self.config = None

    def _create_default_config(self):
        """创建默认配置"""
        default = {
            "access_key_id": "YOUR_KEY",
            "access_key_secret": "YOUR_SECRET",
            "domain": "example.com",
            "records": [{"rr": "www", "type": "A"}]
        }
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(default, f)
        log_message("已创建默认配置")

    def _create_icon(self, color="#4CAF50"):
        """创建图标"""
        img = Image.new('RGBA', (64, 64))
        draw = ImageDraw.Draw(img)
        draw.ellipse((4, 4, 60, 60), fill=color)
        draw.text((16, 24), "DNS", fill="white")
        return img.resize((32, 32))

    def _create_menu(self):
        """创建菜单"""
        return pystray.Menu(
            pystray.MenuItem("立即同步", self._sync),
            pystray.MenuItem("查看记录", self._show_records),
            pystray.MenuItem("编辑配置", self._edit_config),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self.quit)
        )

    def run(self):
        """启动"""
        threading.Thread(target=self._worker, daemon=True).start()
        self.icon.run()

    def _worker(self):
        """后台工作线程"""
        while self.running:
            try:
                # 检查配置更新
                if os.path.exists(CONFIG_FILE):
                    mtime = os.path.getmtime(CONFIG_FILE)
                    if mtime > self.config_mtime:
                        self._load_config()
                        self.icon.notify("配置已更新")
                # 自动同步
                if self.config and time.time() % self.config.get('interval', 300) < 10:
                    self._sync_once()
                time.sleep(10)
            except Exception as e:
                log_message(f"工作线程错误: {e}", logging.ERROR)
                time.sleep(30)

    def _sync_once(self):
        """执行同步"""
        try:
            if core.sync_records(self.config):
                self.icon.title = f"{APP_NAME} - 已同步"
                self.icon.icon = self._create_icon("#4CAF50")
            else:
                self.icon.icon = self._create_icon("#F44336")
        except Exception as e:
            log_message(f"同步错误: {e}", logging.ERROR)

    def _sync(self, icon, item):
        """手动同步"""
        threading.Thread(target=self._sync_once, daemon=True).start()

    def _show_records(self, icon, item):
        """显示记录"""
        try:
            client = core.AcsClient(
                self.config['access_key_id'],
                self.config['access_key_secret']
            )
            msg = []
            for r in self.config['records']:
                rec = core.get_dns_record(client, self.config['domain'], r['rr'], r['type'])
                if rec:
                    msg.append(f"{rec['RR']}: {rec['Value']}")
            self._msg("DNS记录", "\n".join(msg) or "无记录")
        except Exception as e:
            self._msg("错误", "获取记录失败")

    def _edit_config(self, icon, item):
        """编辑配置"""
        try:
            cmd = {
                "Windows": ["notepad", CONFIG_FILE],
                "Darwin": ["open", CONFIG_FILE],
            }.get(platform.system(), ["xdg-open", CONFIG_FILE])
            subprocess.run(cmd)
        except Exception:
            self._msg("错误", "无法打开配置")

    def _msg(self, title, msg):
        """显示消息"""
        root = Tk()
        root.withdraw()
        messagebox.showinfo(title, msg)
        root.destroy()

    def quit(self, icon, item):
        """退出"""
        self.running = False
        self.icon.stop()

if __name__ == '__main__':
    try:
        DDNSTrayApp().run()
    except Exception as e:
        log_message(f"启动失败: {e}", logging.ERROR)
        sys.exit(1)
