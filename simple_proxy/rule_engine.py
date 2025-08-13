import re
from typing import Dict, Optional

class RuleEngine:
    def __init__(self, config):
        self.config = config
        self._compile_rules()
        
    def _compile_rules(self):
        self.compiled_rules = []
        for rule in self.config.get_rules():
            try:
                pattern = re.compile(rule["pattern"])
                self.compiled_rules.append((pattern, rule))
            except re.error:
                print(f"Invalid regex pattern: {rule['pattern']}")
                
    def evaluate(self, ip: str) -> Dict:
        """
        Evaluate an IP address against the rules and return the matching action
        """
        for pattern, rule in self.compiled_rules:
            if pattern.match(ip):
                return rule
                
        # Return default mode if no rules match
        return {"action": self.config.config["default_mode"]}
    
    def get_proxy_for_ip(self, ip: str) -> Optional[Dict]:
        """
        Get the proxy configuration for a given IP address
        """
        rule = self.evaluate(ip)
        if rule["action"] == "proxy" and "proxy" in rule:
            return self.config.get_proxy_settings(rule["proxy"])
        elif rule["action"] == "proxy":
            return self.config.get_proxy_settings()
        return None