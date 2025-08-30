# 阿里云 DDNS 使用指南

## 安装

1. 克隆或下载项目到本地
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 配置

1. 编辑 `config.yaml` 文件，填入您的阿里云访问密钥和域名信息：
   ```yaml
   access_key_id: 'your-access_key_id'
   access_key_secret: 'your-access_key_secret'
   domain: your-domain.com
   records:
     - rr: '@'
       type: 'A'  # 或 'AAAA' 用于 IPv6
   interval: 300
   ttl: 600
   ```

2. 配置项说明：
   - `access_key_id` 和 `access_key_secret`：阿里云账号的访问密钥
   - `domain`：要进行动态解析的域名
   - `records`：要同步的 DNS 记录列表
   - `interval`：自动同步的时间间隔（秒）
   - `ttl`：DNS 记录的生存时间（秒）

## 使用方法

### 命令行模式

```bash
# 使用默认配置文件
python run_core.py

# 使用指定配置文件
python run_core.py -c /path/to/your/config.yaml

# 详细日志模式
python run_core.py -v
```

### GUI 模式

```bash
python run_gui.py
```

GUI 模式启动后会在系统托盘显示一个图标，右键点击可以：
- **立即同步**：手动触发同步
- **查看记录**：查看当前 DNS 记录
- **编辑配置**：打开配置文件编辑
- **退出**：关闭程序

## 开发

### 项目结构

```
aliyun_ddns/
├── aliyun_ddns/        # 主要代码包
│   ├── __init__.py     # 包初始化文件
│   ├── core.py         # 核心功能模块
│   └── gui.py          # 图形界面模块
├── tests/              # 测试文件
│   ├── __init__.py
│   ├── test_core.py
│   └── test_config.py
├── config.yaml         # 配置文件
├── requirements.txt    # 依赖列表
├── setup.py            # 安装脚本
├── run_core.py         # 命令行入口
├── run_gui.py          # GUI 入口
├── README.md           # 项目说明
└── USAGE.md            # 使用指南
```

### 运行测试

```bash
python -m pytest tests/
```

### 代码规范

- 遵循 PEP 8 代码规范
- 函数和类需要有适当的文档字符串
- 添加新功能时需要编写相应的测试

## 故障排除

### 常见问题

1. **配置文件错误**：
   - 确保配置文件格式正确（YAML 格式）
   - 确保必填字段都已填写
   - 确保记录类型为 A 或 AAAA

2. **权限问题**：
   - 确保阿里云访问密钥具有 DNS 管理权限
   - 确保域名已在阿里云解析

3. **网络问题**：
   - 确保可以访问阿里云 API
   - 确保可以访问公网 IP 查询服务

### 查看日志

程序运行时会生成日志文件：
- 命令行模式：输出到控制台
- GUI 模式：记录到 `aliyun_ddns.log` 文件

## 贡献

欢迎提交 Issue 和 Pull Request 来改进项目。