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
    
    def save_config(self) -> None:
        with open(self.config_path, 'w') as f:
            if self.config_path.endswith('.json'):
                json.dump(self.config, f, indent=2)
            else:
                yaml.safe_dump(self.config, f)
    
    def add_rule(self, pattern: str, action: str, proxy: Optional[str] = None) -> None:
        rule = {"pattern": pattern, "action": action}
        if proxy:
            rule["proxy"] = proxy
        self.config["rules"].append(rule)
        self.save_config()
    
    def remove_rule(self, pattern: str) -> bool:
        initial_length = len(self.config["rules"])
        self.config["rules"] = [r for r in self.config["rules"] if r["pattern"] != pattern]
        if len(self.config["rules"]) != initial_length:
            self.save_config()
            return True
        return False
    
    def get_rules(self) -> List[Dict]:
        return self.config["rules"]
    
    def get_proxy_settings(self, proxy_name: str = "default_proxy") -> Dict:
        return self.config["proxy_settings"].get(proxy_name)