import asyncio
import subprocess
import logging
from typing import List, Dict, Optional
import os
import signal

logger = logging.getLogger(__name__)

class SSHForwarder:
    def __init__(self, config):
        self.config = config
        self.forwarding_processes = {}  # 存储SSH进程
        
    def get_ssh_configs(self) -> List[Dict]:
        """获取SSH转发配置"""
        return self.config.config.get("ssh_forwarding", [])
    
    async def start_all_forwarding(self):
        """启动所有SSH端口转发"""
        ssh_configs = self.get_ssh_configs()
        for config in ssh_configs:
            if config.get("enabled", True):
                await self.start_forwarding(config)
    
    async def start_forwarding(self, ssh_config: Dict):
        """启动单个SSH端口转发"""
        try:
            local_port = ssh_config["local_port"]
            remote_host = ssh_config["remote_host"]
            remote_port = ssh_config["remote_port"]
            ssh_host = ssh_config["ssh_host"]
            ssh_port = ssh_config.get("ssh_port", 22)
            ssh_user = ssh_config["ssh_user"]
            name = ssh_config.get("name", f"{local_port}->{ssh_host}")
            
            # 构建SSH命令
            ssh_cmd = [
                "ssh",
                "-R", f"{remote_port}:{remote_host}:{local_port}",
                "-N",  # 不执行远程命令
                "-o", "ServerAliveInterval=60",  # 保持连接
                "-o", "ServerAliveCountMax=3",
                "-o", "StrictHostKeyChecking=no",
                "-p", str(ssh_port),
                f"{ssh_user}@{ssh_host}"
            ]
            
            logger.info(f"启动SSH转发: {name} - {' '.join(ssh_cmd)}")
            
            # 启动SSH进程
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.forwarding_processes[name] = {
                "process": process,
                "config": ssh_config,
                "pid": process.pid
            }
            
            # 异步监控进程状态
            asyncio.create_task(self._monitor_process(name, process))
            
            logger.info(f"SSH转发已启动: {name} (PID: {process.pid})")
            
        except Exception as e:
            logger.error(f"启动SSH转发失败: {e}")
    
    async def _monitor_process(self, name: str, process: asyncio.subprocess.Process):
        """监控SSH进程状态"""
        try:
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"SSH转发进程异常退出: {name} - {error_msg}")
                
                # 从进程列表中移除
                if name in self.forwarding_processes:
                    del self.forwarding_processes[name]
                    
                # 如果配置为自动重启，则重新启动
                config = None
                for proc_info in self.forwarding_processes.values():
                    if proc_info.get("config", {}).get("name") == name:
                        config = proc_info["config"]
                        break
                
                if config and config.get("auto_restart", True):
                    logger.info(f"自动重启SSH转发: {name}")
                    await asyncio.sleep(5)  # 等待5秒后重启
                    await self.start_forwarding(config)
            
        except Exception as e:
            logger.error(f"监控SSH进程时出错: {name} - {e}")
    
    async def stop_forwarding(self, name: str):
        """停止指定的SSH端口转发"""
        if name in self.forwarding_processes:
            proc_info = self.forwarding_processes[name]
            process = proc_info["process"]
            
            try:
                # 发送终止信号
                process.terminate()
                
                # 等待进程结束
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # 强制杀死进程
                    process.kill()
                    await process.wait()
                
                logger.info(f"SSH转发已停止: {name}")
                
            except Exception as e:
                logger.error(f"停止SSH转发时出错: {name} - {e}")
            
            del self.forwarding_processes[name]
    
    async def stop_all_forwarding(self):
        """停止所有SSH端口转发"""
        names = list(self.forwarding_processes.keys())
        for name in names:
            await self.stop_forwarding(name)
    
    def get_status(self) -> Dict:
        """获取所有SSH转发的状态"""
        status = {}
        for name, proc_info in self.forwarding_processes.items():
            process = proc_info["process"]
            config = proc_info["config"]
            
            status[name] = {
                "pid": proc_info["pid"],
                "running": process.returncode is None,
                "local_port": config["local_port"],
                "remote_port": config["remote_port"],
                "ssh_host": config["ssh_host"],
                "ssh_user": config["ssh_user"]
            }
        
        return status
    
    async def restart_forwarding(self, name: str):
        """重启指定的SSH端口转发"""
        if name in self.forwarding_processes:
            config = self.forwarding_processes[name]["config"]
            await self.stop_forwarding(name)
            await asyncio.sleep(1)
            await self.start_forwarding(config)
        else:
            logger.warning(f"SSH转发不存在: {name}")