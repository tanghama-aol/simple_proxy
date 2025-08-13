"""
规则引擎模块

负责管理和执行代理规则，包括：
- 规则解析和验证
- 规则匹配和应用
- 规则优先级处理
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional

from .config import Config

class Rule:
    def __init__(self, pattern: str, target: str, priority: int = 0):
        """
        初始化规则
        :param pattern: 匹配模式（支持正则表达式）
        :param target: 目标地址（格式：host:port）
        :param priority: 规则优先级（数字越大优先级越高）
        """
        self.pattern = pattern
        self.target = target
        self.priority = priority
        self.regex = re.compile(pattern)
        
        # 解析目标地址
        host_port = target.split(':')
        self.target_host = host_port[0]
        self.target_port = int(host_port[1]) if len(host_port) > 1 else 80

class RuleEngine:
    def __init__(self, config: Config):
        self.config = config
        self.rules: List[Rule] = []
        self.logger = logging.getLogger(__name__)
        self._load_rules()

    def _load_rules(self) -> None:
        """从配置加载规则"""
        rules_config = self.config.get('rules', [])
        for rule_data in rules_config:
            try:
                rule = Rule(
                    pattern=rule_data['pattern'],
                    target=rule_data['target'],
                    priority=rule_data.get('priority', 0)
                )
                self.rules.append(rule)
            except Exception as e:
                self.logger.error(f"加载规则失败: {str(e)}")

        # 按优先级排序规则
        self.rules.sort(key=lambda x: x.priority, reverse=True)

    def add_rule(self, pattern: str, target: str, priority: int = 0) -> None:
        """添加新规则
        :param pattern: 匹配模式
        :param target: 目标地址
        :param priority: 优先级
        """
        rule = Rule(pattern, target, priority)
        self.rules.append(rule)
        self.rules.sort(key=lambda x: x.priority, reverse=True)
        
        # 更新配置
        rules_config = self.config.get('rules', [])
        rules_config.append({
            'pattern': pattern,
            'target': target,
            'priority': priority
        })
        self.config.set('rules', rules_config)

    def remove_rule(self, pattern: str) -> None:
        """删除规则
        :param pattern: 要删除的规则模式
        """
        self.rules = [r for r in self.rules if r.pattern != pattern]
        
        # 更新配置
        rules_config = self.config.get('rules', [])
        rules_config = [r for r in rules_config if r['pattern'] != pattern]
        self.config.set('rules', rules_config)

    async def apply_rules(self, data: bytes) -> Tuple[str, int]:
        """应用规则处理请求
        :param data: 请求数据
        :return: (目标主机, 目标端口)
        """
        request_str = data.decode('utf-8', errors='ignore')
        
        for rule in self.rules:
            if rule.regex.search(request_str):
                self.logger.debug(f"匹配到规则: {rule.pattern} -> {rule.target}")
                return rule.target_host, rule.target_port
        
        # 如果没有匹配的规则，解析原始请求中的目标地址
        try:
            host_line = re.search(r'Host: (.*?)\r\n', request_str)
            if host_line:
                host = host_line.group(1)
                if ':' in host:
                    host, port = host.split(':')
                    return host, int(port)
                return host, 80
        except Exception as e:
            self.logger.error(f"解析请求目标地址失败: {str(e)}")
        
        # 默认返回
        return 'localhost', 80