import asyncio
import click
from .config import ProxyConfig
from .proxy_server import ProxyServer
from .web_interface import WebInterface

@click.command()
@click.option('--config', default='config.yaml', help='Path to configuration file')
@click.option('--proxy-host', default='127.0.0.1', help='Proxy server host')
@click.option('--proxy-port', default=8080, help='Proxy server port')
@click.option('--web-host', default='127.0.0.1', help='Web interface host')
@click.option('--web-port', default=8081, help='Web interface port')
def main(config, proxy_host, proxy_port, web_host, web_port):
    """Simple Proxy Server with web configuration interface"""
    config = ProxyConfig(config)
    
    # Create proxy server and web interface
    proxy_server = ProxyServer(config, proxy_host, proxy_port)
    web_interface = WebInterface(config, web_host, web_port)
    
    # Run both servers
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(
            proxy_server.start(),
            web_interface.start()
        ))
        print(f"Proxy server running on http://{proxy_host}:{proxy_port}")
        print(f"Web interface running on http://{web_host}:{web_port}")
        loop.run_forever()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
    finally:
        loop.close()

if __name__ == '__main__':
    main()