# 阿里云 DDNS 项目

## 项目概述
本项目是一个基于阿里云 API 的动态域名解析（DDNS）工具，具备图形化用户界面（GUI），通过系统托盘图标提供便捷操作。它能够自动检测公网 IP 地址的变化，并及时更新阿里云 DNS 记录，确保域名始终指向最新的公网 IP 地址。

## 功能特性
- **自动同步**：按照预设的时间间隔自动检测公网 IP 变化，并同步到阿里云 DNS 记录。
- **手动同步**：支持通过系统托盘菜单手动触发 IP 同步操作。
- **配置编辑**：可以直接在系统托盘菜单中打开配置文件进行编辑。
- **记录查看**：方便查看当前阿里云 DNS 记录的详细信息。
- **配置更新提醒**：当配置文件发生更改时，会自动重新加载并给出通知。

## 环境要求
- Python 3.11.x
- 安装必要的 Python 库：
  - `aliyun-python-sdk-core`
  - `aliyun-python-sdk-alidns`
  - `pystray`
  - `Pillow`
  - `requests`
  - `PyYAML`

你可以使用以下命令安装这些依赖：
```bash
pip install aliyun-python-sdk-core aliyun-python-sdk-alidns pystray Pillow requests PyYAML
```

## 配置说明
在项目根目录下，有一个 `config.yaml` 文件，用于配置阿里云账号信息和 DNS 记录。以下是一个示例配置：
```yaml
access_key_id: 'youraccess_key_id'
access_key_secret: 'youraccess_key_secret'
domain:
records:
  - rr: '@' 
    type: 'A' ）
interval: 300  
ttl: 600
```
- `access_key_id` 和 `access_key_secret`：阿里云账号的访问密钥，用于身份验证。
- `domain`：要进行动态解析的域名。
- `records`：一个列表，包含要同步的 DNS 记录。每个记录包含 `rr`（主机记录）和 `type`（记录类型，支持 `A` 和 `AAAA`）。
- `interval`：自动同步的时间间隔，单位为秒，默认为 300 秒。
- `ttl`：DNS 记录的生存时间，单位为秒，默认为 600 秒。

## 使用方法
### 1. 克隆项目
首先，将项目克隆到本地
### 2. 配置文件
打开 `config.yaml` 文件，将 `access_key_id` 和 `access_key_secret` 替换为你自己的阿里云访问密钥，同时根据需要修改 `domain` 和 `records` 配置。

### 3. 运行项目
在终端中运行以下命令启动程序：
```bash
python aliyun_ddns_gui.py
```
程序启动后，会在系统托盘显示一个图标，右键单击该图标可以进行各种操作：
- **立即同步**：手动触发公网 IP 同步到阿里云 DNS 记录。
- **查看记录**：查看当前阿里云 DNS 记录的详细信息。
- **编辑配置**：打开 `config.yaml` 文件进行编辑。
- **退出**：关闭程序。

### 4. 日志查看
程序运行过程中的日志信息会记录在 `aliyun_ddns.log` 文件中，你可以通过查看该文件来了解程序的运行状态和可能出现的错误信息。

## 注意事项
- 请确保你的阿里云账号具有足够的权限来管理 DNS 记录。
- 如果在使用过程中遇到问题，可以查看日志文件以获取更多详细信息。
- 配置文件修改后，程序会自动检测并重新加载配置。

## 贡献
如果你对本项目有任何建议或发现了 bug，欢迎提交 issue 或 pull request。我们非常感谢你的贡献！
