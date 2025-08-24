import re
from typing import Dict, Optional
from urllib.parse import urlparse

class RuleEngine:
    def __init__(self, config):
        self.config = config
        self._compile_rules()
        
    def _compile_rules(self):
        self.compiled_rules = []
        for rule in self.config.get_rules():
            try:
                # 支持通配符模式转换为正则表达式
                pattern_str = rule["pattern"]
                if rule.get("type") == "domain":
                    # 域名匹配，支持 *.example.com 格式
                    pattern_str = pattern_str.replace("*", ".*").replace(".", r"\.")
                    pattern_str = f"^{pattern_str}$"
                pattern = re.compile(pattern_str)
                self.compiled_rules.append((pattern, rule))
            except re.error:
                print(f"Invalid regex pattern: {rule['pattern']}")
    
    def evaluate_domain(self, domain: str) -> Dict:
        """
        基于域名评估规则并返回匹配的动作
        """
        for pattern, rule in self.compiled_rules:
            if rule.get("type") == "domain" and pattern.match(domain):
                return rule
                
        # 如果没有规则匹配，返回默认模式
        return {"action": self.config.config["default_mode"]}
                
    def evaluate_ip(self, ip: str) -> Dict:
        """
        基于IP地址评估规则并返回匹配的动作
        """
        for pattern, rule in self.compiled_rules:
            if rule.get("type") == "ip" and pattern.match(ip):
                return rule
                
        # 如果没有规则匹配，返回默认模式
        return {"action": self.config.config["default_mode"]}
    
    def get_proxy_for_request(self, url: str, client_ip: str = None) -> Optional[Dict]:
        """
        根据URL和客户端IP获取代理配置
        """
        parsed_url = urlparse(url)
        domain = parsed_url.hostname or parsed_url.netloc
        
        # 首先尝试域名匹配
        if domain:
            rule = self.evaluate_domain(domain)
            if rule.get("action") != self.config.config["default_mode"]:
                return self._get_proxy_from_rule(rule)
        
        # 如果域名匹配失败，尝试IP匹配
        if client_ip:
            rule = self.evaluate_ip(client_ip)
            return self._get_proxy_from_rule(rule)
        
        # 使用默认规则
        default_rule = {"action": self.config.config["default_mode"]}
        return self._get_proxy_from_rule(default_rule)
    
    def _get_proxy_from_rule(self, rule: Dict) -> Optional[Dict]:
        """
        从规则中获取代理配置
        """
        if rule["action"] == "proxy" and "proxy" in rule:
            return self.config.get_proxy_settings(rule["proxy"])
        elif rule["action"] == "proxy":
            return self.config.get_proxy_settings()
        return None
    
    # 保持向后兼容
    def evaluate(self, ip: str) -> Dict:
        """已废弃：为了向后兼容而保留"""
        return self.evaluate_ip(ip)
    
    def get_proxy_for_ip(self, ip: str) -> Optional[Dict]:
        """已废弃：为了向后兼容而保留"""
        rule = self.evaluate_ip(ip)
        return self._get_proxy_from_rule(rule)