import subprocess
from typing import List, Optional, Tuple
import logging
import os
import sys

class ADBController:
    def __init__(self, adb_path: Optional[str] = None):
        """初始化ADB控制器
        
        Args:
            adb_path: ADB可执行文件的路径，如果为None则使用PATH中的adb
        """
        self.adb_path = adb_path if adb_path else 'adb'
        self._setup_logging()
    
    def _setup_logging(self):
        """配置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('ADBController')
    
    def _run_command(self, command: List[str]) -> Tuple[bool, str]:
        """执行ADB命令
        
        Args:
            command: 要执行的命令和参数列表
        
        Returns:
            (成功与否, 输出结果)
        """
        try:
            full_command = [self.adb_path] + command
            self.logger.debug(f"Executing command: {' '.join(full_command)}")
            
            # 在Windows上运行adb.exe时添加CREATE_NO_WINDOW标志以避免控制台窗口闪烁
            if sys.platform == "win32" and self.adb_path.endswith('.exe'):
                # Windows平台且是exe文件，添加CREATE_NO_WINDOW标志
                creation_flags = subprocess.CREATE_NO_WINDOW
            else:
                creation_flags = 0
            
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                creationflags=creation_flags  # 添加此参数以避免控制台窗口闪烁
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                self.logger.error(f"Command failed: {result.stderr}")
                return False, result.stderr
                
        except Exception as e:
            self.logger.error(f"Error executing command: {str(e)}")
            return False, str(e)
    
    def get_devices(self) -> List[str]:
        """获取已连接的设备列表
        
        Returns:
            设备ID列表
        """
        success, output = self._run_command(['devices'])
        if not success:
            return []
        
        devices = []
        for line in output.splitlines()[1:]:  # Skip first line (adb devices header)
            if line.strip():
                device_id = line.split()[0]
                devices.append(device_id)
        
        return devices
    
    def pull_file(self, remote_path: str, local_path: str) -> bool:
        """从设备拉取文件
        
        Args:
            remote_path: 设备上的文件路径
            local_path: 本地保存路径
        
        Returns:
            是否成功
        """
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        success, _ = self._run_command(['pull', remote_path, local_path])
        return success
    
    def push_file(self, local_path: str, remote_path: str) -> bool:
        """推送文件到设备
        
        Args:
            local_path: 本地文件路径
            remote_path: 设备上的保存路径
        
        Returns:
            是否成功
        """
        success, _ = self._run_command(['push', local_path, remote_path])
        return success
    
    def execute_shell_command(self, command: str) -> Tuple[bool, str]:
        """在设备上执行shell命令
        
        Args:
            command: 要执行的shell命令
        
        Returns:
            (成功与否, 输出结果)
        """
        return self._run_command(['shell', command])
    
    def get_device_info(self) -> dict:
        """获取设备信息
        
        Returns:
            包含设备信息的字典
        """
        info = {}
        
        # 获取设备型号
        success, model = self.execute_shell_command('getprop ro.product.model')
        if success:
            info['model'] = model.strip()
        
        # 获取Android版本
        success, version = self.execute_shell_command('getprop ro.build.version.release')
        if success:
            info['android_version'] = version.strip()
        
        # 获取序列号
        success, serial = self.execute_shell_command('getprop ro.serialno')
        if success:
            info['serial'] = serial.strip()
        
        return info
