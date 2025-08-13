import asyncio
import aiohttp
from aiohttp import web
import logging
from typing import Optional, Dict
from .rule_engine import RuleEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyServer:
    def __init__(self, config, host: str = "127.0.0.1", port: int = 8080):
        self.config = config
        self.rule_engine = RuleEngine(config)
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_route('*', '/{path:.*}', self.handle_request)
        
    async def handle_request(self, request: web.Request) -> web.Response:
        target_host = request.headers.get('Host', '')
        try:
            # Get client's IP
            client_ip = request.remote
            
            # Determine proxy settings based on rules
            proxy_settings = self.rule_engine.get_proxy_for_ip(client_ip)
            
            # Prepare request
            url = str(request.url)
            headers = dict(request.headers)
            
            # Remove hop-by-hop headers
            hop_by_hop = {'Connection', 'Keep-Alive', 'Proxy-Authenticate',
                         'Proxy-Authorization', 'TE', 'Trailers', 'Transfer-Encoding',
                         'Upgrade'}
            for header in hop_by_hop:
                headers.pop(header, None)
            
            # Create client session with or without proxy
            async with aiohttp.ClientSession() as session:
                if proxy_settings:
                    proxy_url = f"http://{proxy_settings['host']}:{proxy_settings['port']}"
                    async with session.request(
                        request.method,
                        url,
                        headers=headers,
                        data=await request.read(),
                        proxy=proxy_url
                    ) as response:
                        body = await response.read()
                        return web.Response(
                            body=body,
                            status=response.status,
                            headers=response.headers
                        )
                else:
                    async with session.request(
                        request.method,
                        url,
                        headers=headers,
                        data=await request.read()
                    ) as response:
                        body = await response.read()
                        return web.Response(
                            body=body,
                            status=response.status,
                            headers=response.headers
                        )
                        
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return web.Response(status=500, text=str(e))
            
    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"Proxy server started on http://{self.host}:{self.port}")
        
    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.start())
            loop.run_forever()
        except KeyboardInterrupt:
            pass