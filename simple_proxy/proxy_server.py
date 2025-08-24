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
        try:
            # 获取目标URL和客户端信息
            target_host = request.headers.get('Host', '')
            client_ip = request.remote
            url = str(request.url)
            
            # 支持CONNECT方法（用于HTTPS代理）
            if request.method == 'CONNECT':
                return await self.handle_connect(request)
            
            # 根据URL和客户端IP确定代理设置
            proxy_settings = self.rule_engine.get_proxy_for_request(url, client_ip)
            
            logger.info(f"Request: {request.method} {url}, Client: {client_ip}, Proxy: {'direct' if not proxy_settings else proxy_settings.get('host')}")
            
            # 准备请求头
            headers = dict(request.headers)
            
            # 移除跳跃式头部
            hop_by_hop = {'Connection', 'Keep-Alive', 'Proxy-Authenticate',
                         'Proxy-Authorization', 'TE', 'Trailers', 'Transfer-Encoding',
                         'Upgrade'}
            for header in hop_by_hop:
                headers.pop(header, None)
            
            # 创建客户端会话并发送请求
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if proxy_settings:
                    # 使用代理
                    proxy_url = f"http://{proxy_settings['host']}:{proxy_settings['port']}"
                    async with session.request(
                        request.method,
                        url,
                        headers=headers,
                        data=await request.read(),
                        proxy=proxy_url,
                        ssl=False  # 允许不安全的SSL连接
                    ) as response:
                        body = await response.read()
                        return web.Response(
                            body=body,
                            status=response.status,
                            headers=response.headers
                        )
                else:
                    # 直接连接
                    async with session.request(
                        request.method,
                        url,
                        headers=headers,
                        data=await request.read(),
                        ssl=False  # 允许不安全的SSL连接
                    ) as response:
                        body = await response.read()
                        return web.Response(
                            body=body,
                            status=response.status,
                            headers=response.headers
                        )
                        
        except Exception as e:
            logger.error(f"Error handling request {url}: {e}")
            return web.Response(status=500, text=str(e))
    
    async def handle_connect(self, request: web.Request) -> web.Response:
        """处理HTTPS CONNECT请求"""
        try:
            host_port = request.path_qs
            client_ip = request.remote
            
            # 构造URL用于规则匹配
            url = f"https://{host_port}"
            proxy_settings = self.rule_engine.get_proxy_for_request(url, client_ip)
            
            logger.info(f"CONNECT: {host_port}, Client: {client_ip}, Proxy: {'direct' if not proxy_settings else proxy_settings.get('host')}")
            
            if proxy_settings:
                # 通过上游代理建立CONNECT隧道
                proxy_host = proxy_settings['host']
                proxy_port = proxy_settings['port']
                
                # 这里需要实现CONNECT隧道转发逻辑
                # 为了简化，暂时返回502
                return web.Response(status=502, text="CONNECT through proxy not implemented yet")
            else:
                # 直接建立CONNECT隧道
                host, port = host_port.split(':')
                port = int(port)
                
                try:
                    # 建立到目标服务器的连接
                    reader, writer = await asyncio.open_connection(host, port)
                    
                    # 返回200 Connection Established
                    transport = request.transport
                    if transport:
                        transport.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                        
                        # 开始数据转发
                        await self._tunnel_data(transport, reader, writer)
                    
                    return web.Response(status=200)
                except Exception as e:
                    logger.error(f"Failed to establish CONNECT tunnel to {host}:{port}: {e}")
                    return web.Response(status=502, text=f"Bad Gateway: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling CONNECT request: {e}")
            return web.Response(status=500, text=str(e))
    
    async def _tunnel_data(self, client_transport, target_reader, target_writer):
        """在客户端和目标服务器之间转发数据"""
        try:
            # 这是一个简化的隧道实现
            # 实际生产环境中需要更完善的双向数据转发
            async def forward_data():
                while True:
                    try:
                        data = await target_reader.read(8192)
                        if not data:
                            break
                        client_transport.write(data)
                    except Exception:
                        break
            
            await forward_data()
        except Exception as e:
            logger.error(f"Error in tunnel data forwarding: {e}")
        finally:
            try:
                target_writer.close()
                await target_writer.wait_closed()
            except Exception:
                pass
            
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