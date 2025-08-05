import subprocess
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from .device_manager import DeviceManager
from .logger import default_logger

@dataclass
class SMSMessage:
    """短信数据类
    
    Attributes:
        address: 发送/接收号码
        body: 短信内容
        date: 时间戳(毫秒)
        type: 类型(1=接收, 2=发送)
    """
    address: str
    body: str
    date: int
    type: int
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'address': self.address,
            'body': self.body,
            'date': self.date,
            'type': self.type,
            'datetime': datetime.fromtimestamp(self.date / 1000).isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SMS':
        """从字典创建短信对象"""
        return cls(
            address=data['address'],
            body=data['body'],
            date=data['date'],
            type=data['type']
        )
        
class SMSReader:
    def __init__(self, device_manager, logger=None):
        """初始化短信读取器
        
        Args:
            device_manager: 设备管理器实例
            logger: 日志记录器实例（可选）
        """
        self.device_manager = device_manager
        self.logger = logger or logging.getLogger(__name__)
        
        # 如果需要配置根日志记录器，可以在这里添加
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
    def _run_query(self, query: str, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """执行内容提供者查询
        
        Args:
            query: 查询语句
            device_id: 设备ID
            
        Returns:
            查询结果列表
        """
        device_arg = ['-s', device_id] if device_id else []
        success, output = self.device_manager._run_adb_command(
            device_arg + ['shell', 'content', 'query', '--uri', query]
        )
        
        if not success:
            self.logger.error(f"查询失败: {output}")
            return []
            
        results = []
        for line in output.splitlines():
            if line.strip():
                try:
                    parts = line.split('Row:')[1].strip().split(',')
                    row_data = {}
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            row_data[key.strip()] = value.strip()
                    results.append(row_data)
                except Exception as e:
                    self.logger.error(f"解析行失败: {line}, 错误: {str(e)}")
                    
        return results
        
    def get_all_sms(self, device_id: Optional[str] = None) -> List[SMSMessage]:
        """获取所有短信
        
        Args:
            device_id: 设备ID
            
        Returns:
            短信对象列表
        """
        # 获取设备ID（如果未提供）
        if not device_id:
            devices = self.device_manager.get_devices()
            if not devices:
                self.logger.error("没有连接的设备")
                return []
            device_id = devices[0]
            
        # 检查权限
        permissions = self.device_manager.get_device_permissions(device_id)
        if not permissions.get('android.permission.READ_SMS', False):
            self.logger.error("没有读取短信权限")
            return []
            
        # 查询短信数据
        query = "content://sms"
        results = self._run_query(query, device_id)
        
        messages = []
        for result in results:
            try:
                message = SMSMessage(
                    address=result.get('address', ''),
                    body=result.get('body', ''),
                    date=int(result.get('date', '0')),
                    type=int(result.get('type', '1'))
                )
                messages.append(message)
            except ValueError as e:
                self.logger.error(f"解析短信数据失败: {str(e)}")
                
        return messages
        
    def get_conversations(self, device_id: Optional[str] = None) -> Dict[str, List[SMSMessage]]:
        """按会话分组获取短信
        
        Args:
            device_id: 设备ID
            
        Returns:
            {电话号码: 短信列表} 的字典
        """
        all_sms = self.get_all_sms(device_id)
        conversations = {}
        
        for sms in all_sms:
            if sms.address not in conversations:
                conversations[sms.address] = []
            conversations[sms.address].append(sms)
            
        # 按时间排序
        for number in conversations:
            conversations[number].sort(key=lambda x: x.date)
            
        return conversations
        
    def search_sms(self, keyword: str, device_id: Optional[str] = None) -> List[SMSMessage]:
        """搜索短信
        
        Args:
            keyword: 搜索关键词
            device_id: 设备ID
            
        Returns:
            匹配的短信列表
        """
        all_sms = self.get_all_sms(device_id)
        keyword = keyword.lower()
        
        return [
            sms for sms in all_sms
            if keyword in sms.body.lower() or keyword in sms.address.lower()
        ]
        
    def get_sms_by_date_range(self, start_date: datetime, end_date: datetime,
                             device_id: Optional[str] = None) -> List[SMSMessage]:
        """获取指定时间范围内的短信
        
        Args:
            start_date: 开始时间
            end_date: 结束时间
            device_id: 设备ID
            
        Returns:
            时间范围内的短信列表
        """
        all_sms = self.get_all_sms(device_id)
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        return [
            sms for sms in all_sms
            if start_ts <= sms.date <= end_ts
        ]
        
    def save_sms(self, messages: List[SMSMessage], output_path: str):
        """保存短信数据到文件
        
        Args:
            messages: 短信列表
            output_path: 输出文件路径
        """
        data = [sms.to_dict() for sms in messages]
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def load_sms(self, input_path: str) -> List[SMSMessage]:
        """从文件加载短信数据
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            短信列表
        """
        if not os.path.exists(input_path):
            return []
            
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [SMS.from_dict(item) for item in data]
        except Exception as e:
            self.logger.error(f"加载短信数据失败: {str(e)}")
            return []
