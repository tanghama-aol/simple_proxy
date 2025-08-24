import json
import os
from typing import Dict, List, Optional
import yaml

class ProxyConfig:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_default_config()
        
    def _load_default_config(self) -> Dict:
        default_config = {
            "default_mode": "direct",
            "proxy_settings": {
                "default_proxy": {
                    "host": "localhost",
                    "port": 8080,
                    "type": "http"
                }
            },
            "rules": []
        }
        
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                if self.config_path.endswith('.json'):
                    loaded_config = json.load(f)
                else:
                    loaded_config = yaml.safe_load(f)
                default_config.update(loaded_config)
                
        return default_config
    
    def save(self) -> None:
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            if self.config_path.endswith('.json'):
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            else:
                yaml.safe_dump(self.config, f, allow_unicode=True, default_flow_style=False)
    
    def add_rule(self, rule: Dict) -> None:
        """添加新规则"""
        self.config["rules"].append(rule)
    
    def remove_rule(self, rule_index: int) -> bool:
        """根据索引删除规则"""
        try:
            if 0 <= rule_index < len(self.config["rules"]):
                self.config["rules"].pop(rule_index)
                return True
            return False
        except (IndexError, TypeError):
            return False
    
    def remove_rule_by_pattern(self, pattern: str) -> bool:
        """根据模式删除规则（保持向后兼容）"""
        initial_length = len(self.config["rules"])
        self.config["rules"] = [r for r in self.config["rules"] if r["pattern"] != pattern]
        return len(self.config["rules"]) != initial_length
    
    def get_rules(self) -> List[Dict]:
        return self.config["rules"]
    
    def get_proxy_settings(self, proxy_name: str = "default_proxy") -> Dict:
        return self.config["proxy_settings"].get(proxy_name)