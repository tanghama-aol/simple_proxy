"""
代理服务器核心模块

实现代理服务器的主要功能，包括：
- HTTP/HTTPS代理
- 请求转发
- 连接管理
"""

import asyncio
import logging
from typing import Optional, Dict, Any

from .config import Config
from .rule_engine import RuleEngine

class ProxyServer:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.rule_engine = RuleEngine(self.config)
        self.server: Optional[asyncio.AbstractServer] = None
        self._setup_logging()

    def _setup_logging(self) -> None:
        """设置日志"""
        logging_config = self.config.get('logging', {})
        logging.basicConfig(
            level=logging_config.get('level', 'INFO'),
            filename=logging_config.get('filename'),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """处理客户端连接"""
        try:
            # 读取客户端请求
            data = await reader.read(8192)
            if not data:
                return

            # 应用规则处理请求
            target_host, target_port = await self.rule_engine.apply_rules(data)
            
            # 连接目标服务器
            target_reader, target_writer = await asyncio.open_connection(
                target_host, target_port)

            # 转发数据
            await self._relay_data(reader, writer, target_reader, target_writer)

        except Exception as e:
            self.logger.error(f"处理请求时发生错误: {str(e)}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def _relay_data(self, client_reader: asyncio.StreamReader,
                         client_writer: asyncio.StreamWriter,
                         target_reader: asyncio.StreamReader,
                         target_writer: asyncio.StreamWriter) -> None:
        """在客户端和目标服务器之间转发数据"""
        async def relay(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            try:
                while True:
                    data = await reader.read(8192)
                    if not data:
                        break
                    writer.write(data)
                    await writer.drain()
            except Exception as e:
                self.logger.error(f"数据转发错误: {str(e)}")

        await asyncio.gather(
            relay(client_reader, target_writer),
            relay(target_reader, client_writer)
        )

    async def start(self) -> None:
        """启动代理服务器"""
        server_config = self.config.get('server', {})
        host = server_config.get('host', '127.0.0.1')
        port = server_config.get('port', 8080)

        self.server = await asyncio.start_server(
            self.handle_client, host, port)

        self.logger.info(f"代理服务器已启动，监听 {host}:{port}")

        async with self.server:
            await self.server.serve_forever()

    async def stop(self) -> None:
        """停止代理服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("代理服务器已停止")
