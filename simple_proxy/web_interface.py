from aiohttp import web
import os
import json

class WebInterface:
    def __init__(self, config, host: str = "127.0.0.1", port: int = 8081, ssh_forwarder=None):
        self.config = config
        self.host = host
        self.port = port
        self.ssh_forwarder = ssh_forwarder
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        # 静态文件和主页
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_static('/static', os.path.join(os.path.dirname(__file__), 'static'))
        
        # 规则管理API
        self.app.router.add_get('/api/rules', self.handle_get_rules)
        self.app.router.add_post('/api/rules', self.handle_add_rule)
        self.app.router.add_delete('/api/rules/{rule_id}', self.handle_delete_rule)
        
        # 配置管理API
        self.app.router.add_get('/api/config', self.handle_get_config)
        self.app.router.add_post('/api/config', self.handle_update_config)
        
        # SSH转发管理API
        if self.ssh_forwarder:
            self.app.router.add_get('/api/ssh/status', self.handle_ssh_status)
            self.app.router.add_post('/api/ssh/start/{name}', self.handle_ssh_start)
            self.app.router.add_post('/api/ssh/stop/{name}', self.handle_ssh_stop)
            self.app.router.add_post('/api/ssh/restart/{name}', self.handle_ssh_restart)
        
    async def handle_index(self, request):
        return web.FileResponse(os.path.join(os.path.dirname(__file__), 'static', 'index.html'))
        
    async def handle_get_rules(self, request):
        return web.json_response(self.config.get_rules())
        
    async def handle_add_rule(self, request):
        """添加新规则"""
        try:
            data = await request.json()
            
            # 验证必需字段
            required_fields = ['pattern', 'type', 'action']
            for field in required_fields:
                if field not in data:
                    return web.json_response({'error': f'Missing required field: {field}'}, status=400)
            
            # 验证类型
            if data['type'] not in ['domain', 'ip']:
                return web.json_response({'error': 'Rule type must be "domain" or "ip"'}, status=400)
            
            # 验证动作
            if data['action'] not in ['direct', 'proxy']:
                return web.json_response({'error': 'Action must be "direct" or "proxy"'}, status=400)
            
            # 如果是代理动作，需要指定代理设置
            if data['action'] == 'proxy' and 'proxy' not in data:
                data['proxy'] = 'default_proxy'
            
            # 添加规则
            self.config.add_rule(data)
            self.config.save()
            
            return web.json_response({'success': True, 'message': '规则添加成功'})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
        
    async def handle_delete_rule(self, request):
        """删除规则"""
        try:
            rule_id = int(request.match_info['rule_id'])
            success = self.config.remove_rule(rule_id)
            
            if success:
                self.config.save()
                return web.json_response({'success': True, 'message': '规则删除成功'})
            else:
                return web.json_response({'error': '规则不存在'}, status=404)
                
        except (ValueError, IndexError):
            return web.json_response({'error': '无效的规则ID'}, status=400)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
        
    async def handle_get_config(self, request):
        """获取完整配置"""
        return web.json_response(self.config.config)
        
    async def handle_update_config(self, request):
        """更新配置"""
        try:
            data = await request.json()
            
            # 更新配置
            if 'default_mode' in data:
                self.config.config['default_mode'] = data['default_mode']
            
            if 'proxy_settings' in data:
                self.config.config['proxy_settings'] = data['proxy_settings']
            
            if 'rules' in data:
                self.config.config['rules'] = data['rules']
            
            # 保存配置
            self.config.save()
            
            return web.json_response({'success': True, 'message': '配置更新成功'})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    # SSH转发相关API
    async def handle_ssh_status(self, request):
        """获取SSH转发状态"""
        if not self.ssh_forwarder:
            return web.json_response({'error': 'SSH forwarder not enabled'}, status=404)
        
        status = self.ssh_forwarder.get_status()
        return web.json_response(status)
    
    async def handle_ssh_start(self, request):
        """启动SSH转发"""
        if not self.ssh_forwarder:
            return web.json_response({'error': 'SSH forwarder not enabled'}, status=404)
        
        name = request.match_info['name']
        
        # 查找配置
        ssh_configs = self.ssh_forwarder.get_ssh_configs()
        config = next((c for c in ssh_configs if c.get('name') == name), None)
        
        if not config:
            return web.json_response({'error': f'SSH config "{name}" not found'}, status=404)
        
        try:
            await self.ssh_forwarder.start_forwarding(config)
            return web.json_response({'success': True, 'message': f'SSH转发 "{name}" 启动成功'})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def handle_ssh_stop(self, request):
        """停止SSH转发"""
        if not self.ssh_forwarder:
            return web.json_response({'error': 'SSH forwarder not enabled'}, status=404)
        
        name = request.match_info['name']
        
        try:
            await self.ssh_forwarder.stop_forwarding(name)
            return web.json_response({'success': True, 'message': f'SSH转发 "{name}" 停止成功'})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def handle_ssh_restart(self, request):
        """重启SSH转发"""
        if not self.ssh_forwarder:
            return web.json_response({'error': 'SSH forwarder not enabled'}, status=404)
        
        name = request.match_info['name']
        
        try:
            await self.ssh_forwarder.restart_forwarding(name)
            return web.json_response({'success': True, 'message': f'SSH转发 "{name}" 重启成功'})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
        
    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"Web interface started on http://{self.host}:{self.port}")
        
    def run(self):
        web.run_app(self.app, host=self.host, port=self.port)