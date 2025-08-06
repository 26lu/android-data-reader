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
            
        return self._parse_query_result(output)
        
    def _parse_query_result(self, result: str) -> List[Dict[str, str]]:
        """解析查询结果
        
        Args:
            result: ADB查询返回的原始结果字符串
            
        Returns:
            解析后的字典列表
        """
        results = []
        lines = result.strip().split('\n')
        
        self.logger.debug(f"解析 {len(lines)} 行查询结果")
        
        for line in lines:
            if line.startswith('Row:'):
                try:
                    # 解析每一行数据
                    parts = line.split('Row:')[1].strip().split(',')
                    row_data = {}
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            row_data[key.strip()] = value.strip()
                    results.append(row_data)
                except (ValueError, IndexError) as e:
                    self.logger.error(f"解析行失败: {line}, 错误: {str(e)}")
                except Exception as e:
                    self.logger.error(f"解析行时出现未预期错误: {line}, 错误: {str(e)}")
                    
        self.logger.debug(f"成功解析 {len(results)} 行数据")
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
        self.logger.info(f"开始保存 {len(messages)} 条短信数据到 {output_path}")
        
        # 输入验证
        if not output_path:
            self.logger.error("输出路径不能为空")
            raise ValueError("输出路径不能为空")
            
        # 确保输出路径在当前目录内，防止路径遍历
        try:
            abs_output_path = os.path.abspath(output_path)
            abs_cwd = os.path.abspath(os.getcwd())
            if not abs_output_path.startswith(abs_cwd):
                self.logger.error("输出路径必须在当前目录内")
                raise ValueError("输出路径必须在当前目录内")
        except Exception as e:
            self.logger.error(f"验证输出路径时出错: {str(e)}")
            raise ValueError(f"输出路径验证失败: {str(e)}")
        
        try:
            data = [sms.to_dict() for sms in messages]
            
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            self.logger.debug(f"创建目录: {os.path.dirname(output_path)}")
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"成功保存 {len(messages)} 条短信数据到 {output_path}")
        except OSError as e:
            self.logger.error(f"保存短信数据到文件时出错: {str(e)}")
            raise IOError(f"保存短信数据失败: {str(e)}")
        except json.JSONEncodeError as e:
            self.logger.error(f"序列化短信数据时出错: {str(e)}")
            raise ValueError(f"短信数据序列化失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"保存短信数据时出现未预期错误: {str(e)}")
            raise RuntimeError(f"保存短信数据时出错: {str(e)}")
            
    def load_sms(self, input_path: str) -> List[SMSMessage]:
        """从文件加载短信数据
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            短信列表
        """
        self.logger.info(f"开始从 {input_path} 加载短信数据")
        
        # 输入验证
        if not input_path:
            self.logger.error("输入路径不能为空")
            return []
            
        if not os.path.exists(input_path):
            self.logger.warning(f"短信数据文件不存在: {input_path}")
            return []
            
        # 确保输入路径在当前目录内，防止路径遍历
        try:
            abs_input_path = os.path.abspath(input_path)
            abs_cwd = os.path.abspath(os.getcwd())
            if not abs_input_path.startswith(abs_cwd):
                self.logger.error("输入路径必须在当前目录内")
                return []
        except Exception as e:
            self.logger.error(f"验证输入路径时出错: {str(e)}")
            return []
            
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            messages = [SMSMessage.from_dict(item) for item in data]
            self.logger.info(f"成功加载 {len(messages)} 条短信数据")
            return messages
        except json.JSONDecodeError as e:
            self.logger.error(f"解析短信数据文件失败: {str(e)}")
            return []
        except OSError as e:
            self.logger.error(f"读取短信数据文件时出错: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"加载短信数据时出现未预期错误: {str(e)}")
            return []
