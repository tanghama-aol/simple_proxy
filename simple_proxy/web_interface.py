from aiohttp import web
import os
import json

class WebInterface:
    def __init__(self, config, host: str = "127.0.0.1", port: int = 8081):
        self.config = config
        self.host = host
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/api/rules', self.handle_get_rules)
        self.app.router.add_post('/api/rules', self.handle_add_rule)
        self.app.router.add_delete('/api/rules/{pattern}', self.handle_delete_rule)
        self.app.router.add_get('/api/config', self.handle_get_config)
        self.app.router.add_static('/static', os.path.join(os.path.dirname(__file__), 'static'))
        
    async def handle_index(self, request):
        return web.FileResponse(os.path.join(os.path.dirname(__file__), 'static', 'index.html'))
        
    async def handle_get_rules(self, request):
        return web.json_response(self.config.get_rules())
        
    async def handle_add_rule(self, request):
        data = await request.json()
        pattern = data.get('pattern')
        action = data.get('action')
        proxy = data.get('proxy')
        
        if not pattern or not action:
            return web.Response(status=400, text="Missing pattern or action")
            
        self.config.add_rule(pattern, action, proxy)
        return web.Response(status=200)
        
    async def handle_delete_rule(self, request):
        pattern = request.match_info['pattern']
        if self.config.remove_rule(pattern):
            return web.Response(status=200)
        return web.Response(status=404)
        
    async def handle_get_config(self, request):
        return web.json_response(self.config.config)
        
    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"Web interface started on http://{self.host}:{self.port}")
        
    def run(self):
        web.run_app(self.app, host=self.host, port=self.port)