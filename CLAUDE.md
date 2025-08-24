# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run with default settings (proxy on :8080, web interface on :8081)
python -m simple_proxy

# Run with SSH port forwarding enabled
python -m simple_proxy --enable-ssh

# Run with custom configuration
python -m simple_proxy --config custom_config.yaml --proxy-port 9090 --web-port 9091

# Run on different network interface
python -m simple_proxy --proxy-host 0.0.0.0 --web-host 0.0.0.0
```

### Development Commands
```bash
# Install in development mode
pip install -e .

# Test code compilation
python -m py_compile simple_proxy/__main__.py
```

## Architecture Overview

这是一个基于Python的代理服务器，具有类似 SwitchyOmega 的Web配置管理功能，支持基于域名和IP的智能路由。

### Core Architecture
- **ProxyServer** (`simple_proxy/proxy_server.py`): 主HTTP/HTTPS代理服务器，使用aiohttp，支持CONNECT隧道
- **RuleEngine** (`simple_proxy/rule_engine.py`): 处理域名和IP模式匹配及路由决策
- **ProxyConfig** (`simple_proxy/config.py`): 配置管理，支持YAML/JSON格式
- **WebInterface** (`simple_proxy/web_interface.py`): REST API和Web UI用于配置管理
- **SSHForwarder** (`simple_proxy/ssh_forwarder.py`): SSH端口转发管理器，支持远程端口映射

### Key Features
1. **双服务器架构**: 同时运行代理服务器（默认:8080）和Web配置界面（默认:8081）
2. **智能路由**: 
   - 基于域名的规则匹配（支持 *.zte.com.cn 等通配符）
   - 基于IP地址的规则匹配
   - 优先域名匹配，后备IP匹配
3. **SSH端口转发**: 自动化SSH隧道管理，支持远程端口映射
4. **配置持久化**: 支持YAML和JSON配置文件格式
5. **Web配置界面**: 实时规则管理，无需重启服务器

### Configuration Structure
配置支持以下结构：
```yaml
default_mode: proxy  # 默认模式：direct 或 proxy
proxy_settings:     # 代理服务器设置
  default_proxy:
    host: proxy.example.com
    port: 8080
    type: http
rules:              # 路由规则
  - pattern: "*.zte.com.cn"
    type: domain
    action: direct
  - pattern: "192\\.168\\.*"
    type: ip  
    action: direct
ssh_forwarding:     # SSH转发配置
  - name: "远程代理转发"
    enabled: true
    local_port: 8080
    remote_port: 10088
    ssh_host: "10.227.157.229"
    ssh_user: "ubuntu"
```

### Entry Points
- 主入口: `simple_proxy/__main__.py` 使用Click CLI
- Web界面API端点: `/api/rules`, `/api/config`, `/api/ssh/*`
- 静态文件: `simple_proxy/static/` 目录

### Development Notes
- 全程使用async/await模式配合aiohttp
- 规则引擎中的正则表达式被缓存以提高性能
- 支持HTTP和HTTPS代理协议，包括CONNECT方法
- SSH转发进程自动监控和重启
- Web界面提供实时规则管理，支持域名和IP双重匹配模式