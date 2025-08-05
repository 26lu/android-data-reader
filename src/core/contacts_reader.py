import subprocess
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from .device_manager import DeviceManager
from .logger import default_logger

@dataclass
class Contact:
    def __init__(self, name: str, phone: str = "", email: str = "", 
                 group: str = "", notes: str = ""):
        self.name = name
        self.phone = phone
        self.email = email
        self.group = group
        self.notes = notes
        
    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'group': self.group,
            'notes': self.notes
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Contact':
        """从字典创建联系人对象"""
        return cls(
            name=data.get('name', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            group=data.get('group', ''),
            notes=data.get('notes', '')
        )

class ContactsReader:
    def __init__(self, device_manager: DeviceManager):
        """初始化通讯录读取器
        
        Args:
            device_manager: 设备管理器实例
        """
        self.device_manager = device_manager
        self.logger = logging.getLogger('ContactsReader')
        
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
                    # 解析输出格式: Row: 0 col1=value1, col2=value2
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
        
    def get_all_contacts(self, device_id: Optional[str] = None) -> List[Contact]:
        """获取所有联系人
        
        Args:
            device_id: 设备ID
            
        Returns:
            联系人对象列表
        """
        contacts = []
        
        # 检查设备连接
        if not device_id:
            devices = self.device_manager.get_devices()
            if not devices:
                self.logger.error("没有连接的设备")
                return []
            device_id = devices[0]
        
        # 检查权限
        permissions = self.device_manager.get_device_permissions(device_id)
        if not permissions.get('android.permission.READ_CONTACTS', False):
            self.logger.error("没有读取通讯录权限")
            return []
            
        # 查询联系人数据
        query = "content://com.android.contacts/data/phones"
        results = self._run_query(query, device_id)
        
        # 处理查询结果
        for result in results:
            contact = Contact(
                name=result.get('display_name', ''),
                phone=result.get('data1', ''),  # data1字段存储电话号码
                email=result.get('data2', ''),  # data2字段可能存储邮箱
                group=result.get('group_name', ''),
                notes=result.get('notes', '')
            )
            contacts.append(contact)
            
        return contacts
        
    def search_contacts(self, keyword: str, device_id: Optional[str] = None) -> List[Contact]:
        """搜索联系人
        
        Args:
            keyword: 搜索关键词
            device_id: 设备ID
            
        Returns:
            匹配的联系人列表
        """
        all_contacts = self.get_all_contacts(device_id)
        results = []
        
        keyword = keyword.lower()
        for contact in all_contacts:
            if (keyword in contact.name.lower() or
                keyword in contact.phone.lower() or
                keyword in contact.email.lower()):
                results.append(contact)
                
        return results
        
    def get_contact_groups(self, device_id: Optional[str] = None) -> List[str]:
        """获取所有联系人分组
        
        Args:
            device_id: 设备ID
            
        Returns:
            分组名称列表
        """
        query = "content://com.android.contacts/groups"
        results = self._run_query(query, device_id)
        
        groups = []
        for result in results:
            if 'group_name' in result:
                groups.append(result['group_name'])
                
        return groups
        
    def get_contacts_in_group(self, group: str, 
                            device_id: Optional[str] = None) -> List[Contact]:
        """获取指定分组中的联系人
        
        Args:
            group: 分组名称
            device_id: 设备ID
            
        Returns:
            分组中的联系人列表
        """
        all_contacts = self.get_all_contacts(device_id)
        return [contact for contact in all_contacts if contact.group == group]
        
    def save_contacts(self, contacts: List[Contact], output_path: str):
        """保存联系人数据到文件
        
        Args:
            contacts: 联系人列表
            output_path: 输出文件路径
        """
        data = [contact.to_dict() for contact in contacts]
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def load_contacts(self, input_path: str) -> List[Contact]:
        """从文件加载联系人数据
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            联系人列表
        """
        if not os.path.exists(input_path):
            return []
            
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [Contact.from_dict(item) for item in data]
        except Exception as e:
            self.logger.error(f"加载联系人数据失败: {str(e)}")
            return []
