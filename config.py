"""
配置管理模块

负责加载和管理代理服务器的配置信息，包括：
- 服务器监听地址和端口
- 路由规则配置
- 日志配置等
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or 'config.yaml'
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """从配置文件加载配置信息"""
        if not Path(self.config_path).exists():
            self.config = self._get_default_config()
            self.save_config()
        else:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
    
    def save_config(self) -> None:
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """返回默认配置"""
        return {
            'server': {
                'host': '127.0.0.1',
                'port': 8080
            },
            'rules': [],
            'logging': {
                'level': 'INFO',
                'filename': 'proxy.log'
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        self.config[key] = value
        self.save_config()