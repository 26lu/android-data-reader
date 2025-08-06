import subprocess
import json
import logging
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from .device_manager import DeviceManager
from .logger import default_logger

@dataclass
class Contact:
    def __init__(self, name: str, phone=None, email=None,
                 group: str = "", notes: str = ""):
        self.name = name
        # 确保电话号码和邮箱始终是列表格式
        if phone is None:
            self.phone = []
        elif isinstance(phone, list):
            self.phone = phone
        else:
            self.phone = [phone] if phone else []

        if email is None:
            self.email = []
        elif isinstance(email, list):
            self.email = email
        else:
            self.email = [email] if email else []

        self.group = group
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'group': self.group,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contact':
        """从字典创建联系人对象"""
        return cls(
            name=data.get('name', ''),
            phone=data.get('phone', []),
            email=data.get('email', []),
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

    def _run_query(self, uri: str, device_id: Optional[str] = None) -> List[Dict[str, str]]:
        """执行ADB内容查询命令

        Args:
            uri: 要查询的内容URI
            device_id: 设备ID

        Returns:
            解析后的结果列表
        """
        if not device_id:
            devices = self.device_manager.get_devices()
            if not devices:
                self.logger.error("没有连接的设备")
                return []
            device_id = devices[0]

        # 构建ADB命令，使用shell执行content query
        cmd = ['shell', 'content', 'query', '--uri', uri]
        success, result = self.device_manager._run_adb_command(cmd, device_id)

        # 打印原始ADB命令输出用于调试
        self.logger.debug(f"ADB命令执行结果 - 成功: {success}")
        self.logger.debug(f"ADB命令原始输出长度: {len(result) if result else 0} 字符")
        self.logger.debug(f"ADB命令原始输出前1000字符: {result[:1000] if result else 'None'}")

        if not success or not result:
            self.logger.warning(f"查询 {uri} 失败或返回空结果")
            return []

        return self._parse_query_result(result)

    def _parse_query_result(self, result: str) -> List[Dict[str, str]]:
        """解析查询结果

        Args:
            result: ADB查询返回的原始结果字符串

        Returns:
            解析后的字典列表
        """
        self.logger.debug(f"开始解析查询结果，输入长度: {len(result)} 字符")

        if not result or not result.strip():
            self.logger.warning("查询结果为空")
            return []

        results = []
        lines = result.strip().split('\n')

        self.logger.debug(f"开始解析 {len(lines)} 行查询结果")

        for i, line in enumerate(lines):
            if line.startswith('Row:'):
                try:
                    # 解析每一行数据
                    # 从"Row: 0 ..."开始解析
                    row_content = line.split('Row:')[1].strip()  # 移除"Row:"前缀

                    # 使用更复杂的解析方法来处理包含逗号的值
                    row_data = self._parse_row_data(row_content)

                    results.append(row_data)
                    # 为前几行添加详细日志
                    if len(results) <= 3:
                        self.logger.debug(f"解析结果 {len(results)}: display_name='{row_data.get('display_name', 'NOT_FOUND')}', display_name_alt='{row_data.get('display_name_alt', 'NOT_FOUND')}'")
                except (ValueError, IndexError) as e:
                    self.logger.error(f"解析行失败: {line}, 错误: {str(e)}")
                except Exception as e:
                    self.logger.error(f"解析行时出现未预期错误: {line}, 错误: {str(e)}")
            else:
                # 为前几行非Row行添加日志
                if i < 5:
                    self.logger.debug(f"跳过非Row行: {line[:50]}...")

        self.logger.info(f"成功解析 {len(results)} 行数据，总共处理 {len(lines)} 行")
        return results

    def _parse_row_data(self, row_content: str) -> Dict[str, str]:
        """解析单行数据

        Args:
            row_content: 行内容字符串

        Returns:
            解析后的字典
        """
        result = {}

        # 简单解析方法：从后往前找等号和逗号
        # 因为值中可能包含逗号，所以我们从后往前处理
        parts = row_content.split(', ')
        i = 0
        while i < len(parts):
            part = parts[i]
            if '=' in part:
                # 找到键值对
                if part.count('=') == 1:
                    # 简单情况：key=value
                    key, value = part.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 处理NULL值
                    if value == 'NULL':
                        value = ''
                    result[key] = value
                else:
                    # 复杂情况：值中包含逗号
                    # 需要合并后续部分直到找到下一个键值对
                    key, value = part.split('=', 1)
                    key = key.strip()

                    # 继续合并后续部分，直到找到下一个包含等号且等号前后都有内容的部分
                    value_parts = [value]
                    j = i + 1
                    while j < len(parts):
                        next_part = parts[j]
                        # 检查这是否是下一个键值对
                        if '=' in next_part and not next_part.startswith('=') and not next_part.endswith('='):
                            # 检查等号前后是否有内容
                            eq_idx = next_part.index('=')
                            if eq_idx > 0 and eq_idx < len(next_part) - 1:
                                # 这是下一个键值对，停止合并
                                break
                        value_parts.append(next_part)
                        j += 1

                    value = ', '.join(value_parts).strip()
                    # 处理NULL值
                    if value == 'NULL':
                        value = ''
                    result[key] = value
                    i = j - 1  # 因为循环会增加i，所以这里减1
            i += 1

        return result


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
            # 检查是否是因为设备未授权导致的权限检查失败
            if 'unauthorized' in str(permissions.get('error', '')).lower():
                self.logger.error("设备未授权，请在手机上确认USB调试授权")
            else:
                self.logger.error("没有读取通讯录权限")
            return []

        # 使用原始的查询方式，直接查询联系人数据表
        query = "content://com.android.contacts/data/phones"
        results = self._run_query(query, device_id)

        self.logger.info(f"从设备 {device_id} 获取到 {len(results)} 条原始联系人数据")

        # 处理查询结果
        for i, result in enumerate(results):

            # 直接使用display_name字段作为姓名
            name = ''
            # 查找包含display_name的键，正确处理"数字 display_name"格式
            for key in result.keys():
                self.logger.debug(f"检查键: '{key}'")
                if key.endswith(' display_name') and not key.endswith(' display_name_alt') and result[key]:
                    name = result[key]
                    break

            # 如果没有找到，尝试display_name_alt
            if not name:
                for key in result.keys():
                    self.logger.debug(f"检查alt键: '{key}'")
                    if key.endswith(' display_name_alt') and result[key]:
                        name = result[key]
                        break


            contact = Contact(
                name=name,
                phone=result.get('data1', ''),  # data1字段存储电话号码
                email='',  # 在这个查询中不包含邮箱
                group=result.get('group_name', ''),
                notes=''
            )
            contacts.append(contact)

        self.logger.info(f"处理后得到 {len(contacts)} 个联系人对象")


        return contacts
