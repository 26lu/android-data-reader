import os
from typing import List, Optional, Dict, Any, Tuple
from .adb_controller import ADBController
from .data_processor import DataProcessor

class AndroidDataReader:
    def __init__(self, cache_dir: Optional[str] = None, adb_path: Optional[str] = None):
        """初始化Android数据读取器
        
        Args:
            cache_dir: 缓存目录路径
            adb_path: ADB可执行文件路径
        """
        self.adb = ADBController(adb_path)
        self.processor = DataProcessor(cache_dir)
        
    def check_device_connection(self) -> Tuple[bool, List[str]]:
        """检查设备连接状态
        
        Returns:
            (是否有设备连接, 设备列表)
        """
        devices = self.adb.get_devices()
        return len(devices) > 0, devices
    
    def get_device_info(self) -> Dict[str, str]:
        """获取设备信息
        
        Returns:
            设备信息字典
        """
        return self.adb.get_device_info()
    
    def read_file(self, remote_path: str) -> Optional[str]:
        """读取设备上的文件内容
        
        Args:
            remote_path: 设备上的文件路径
        
        Returns:
            文件内容，如果读取失败则返回None
        """
        # 创建临时文件路径
        local_path = os.path.join(
            self.processor.cache_dir,
            os.path.basename(remote_path)
        )
        
        # 拉取文件
        if not self.adb.pull_file(remote_path, local_path):
            return None
        
        try:
            with open(local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            print(f"Error reading file {local_path}: {str(e)}")
            return None
        finally:
            # 清理临时文件
            if os.path.exists(local_path):
                os.remove(local_path)
    
    def read_image(self, remote_path: str) -> Optional[str]:
        """读取设备上的图片
        
        Args:
            remote_path: 设备上的图片路径
        
        Returns:
            处理后的图片保存路径，如果处理失败则返回None
        """
        # 创建临时文件路径
        temp_path = os.path.join(
            self.processor.cache_dir,
            os.path.basename(remote_path)
        )
        
        # 拉取图片
        if not self.adb.pull_file(remote_path, temp_path):
            return None
        
        try:
            # 处理图片
            image = self.processor.process_image(temp_path)
            if image is None:
                return None
            
            # 保存处理后的图片
            output_path = os.path.join(
                self.processor.cache_dir,
                f"processed_{os.path.basename(remote_path)}"
            )
            if self.processor.save_processed_image(image, output_path):
                return output_path
            return None
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def read_json_data(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """读取设备上的JSON数据
        
        Args:
            remote_path: 设备上的JSON文件路径
        
        Returns:
            解析后的数据字典，如果处理失败则返回None
        """
        content = self.read_file(remote_path)
        if content is None:
            return None
        
        return self.processor.process_json_data(content)
    
    def execute_command(self, command: str) -> Tuple[bool, str]:
        """在设备上执行命令
        
        Args:
            command: 要执行的shell命令
        
        Returns:
            (成功与否, 输出结果)
        """
        return self.adb.execute_shell_command(command)
    
    def cleanup(self):
        """清理缓存"""
        self.processor.clean_cache()
