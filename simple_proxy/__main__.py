import asyncio
import click
from .config import ProxyConfig
from .proxy_server import ProxyServer
from .web_interface import WebInterface
from .ssh_forwarder import SSHForwarder

@click.command()
@click.option('--config', default='config.yaml', help='配置文件路径')
@click.option('--proxy-host', default='127.0.0.1', help='代理服务器主机')
@click.option('--proxy-port', default=8080, help='代理服务器端口')
@click.option('--web-host', default='127.0.0.1', help='Web界面主机')
@click.option('--web-port', default=8081, help='Web界面端口')
@click.option('--enable-ssh', is_flag=True, help='启用SSH端口转发')
def main(config, proxy_host, proxy_port, web_host, web_port, enable_ssh):
    """Simple Proxy Server with web configuration interface"""
    # 加载配置
    config_obj = ProxyConfig(config)
    
    # 创建组件
    proxy_server = ProxyServer(config_obj, proxy_host, proxy_port)
    ssh_forwarder = SSHForwarder(config_obj) if enable_ssh else None
    web_interface = WebInterface(config_obj, web_host, web_port, ssh_forwarder)
    
    # 运行所有服务
    loop = asyncio.get_event_loop()
    try:
        # 启动服务
        tasks = [
            proxy_server.start(),
            web_interface.start()
        ]
        
        if ssh_forwarder:
            tasks.append(ssh_forwarder.start_all_forwarding())
        
        loop.run_until_complete(asyncio.gather(*tasks))
        
        print(f"代理服务器运行在 http://{proxy_host}:{proxy_port}")
        print(f"Web配置界面运行在 http://{web_host}:{web_port}")
        
        if ssh_forwarder:
            ssh_status = ssh_forwarder.get_status()
            if ssh_status:
                print("SSH端口转发状态:")
                for name, status in ssh_status.items():
                    print(f"  {name}: {'运行中' if status['running'] else '已停止'} (PID: {status.get('pid', 'N/A')})")
        
        # 设置信号处理
        def signal_handler():
            print("\n正在关闭服务器...")
            if ssh_forwarder:
                loop.run_until_complete(ssh_forwarder.stop_all_forwarding())
            loop.stop()
        
        # 在Windows上使用不同的信号处理方式
        try:
            import signal
            for sig in [signal.SIGTERM, signal.SIGINT]:
                loop.add_signal_handler(sig, signal_handler)
        except (ImportError, NotImplementedError):
            # Windows不支持add_signal_handler
            pass
        
        loop.run_forever()
        
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        if ssh_forwarder:
            loop.run_until_complete(ssh_forwarder.stop_all_forwarding())
    finally:
        loop.close()

if __name__ == '__main__':
    main()