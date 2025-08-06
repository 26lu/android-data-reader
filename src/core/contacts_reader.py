import subprocess
import json
import logging
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from .device_manager import DeviceManager
from .logger import default_logger
import re

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

    def _normalize_name(self, name: str) -> str:
        """标准化姓名，用于比较

        Args:
            name: 原始姓名

        Returns:
            标准化后的姓名
        """
        if not name:
            return ""
        # 移除空格和其他分隔符，统一小写进行比较
        return ''.join(name.lower().split())

    def _normalize_phone(self, phone: str) -> str:
        """标准化电话号码，移除空格、破折号等分隔符以便比较

        Args:
            phone: 原始电话号码

        Returns:
            标准化后的电话号码
        """
        if not phone:
            return ""
        # 移除所有非数字字符
        return ''.join(filter(str.isdigit, phone))

    def _should_merge_contacts(self, contact1: Contact, contact2: Contact) -> bool:
        """判断两个联系人是否应该合并

        Args:
            contact1: 第一个联系人
            contact2: 第二个联系人

        Returns:
            是否应该合并
        """
        # 如果电话号码相同，则合并
        for phone1 in contact1.phone:
            for phone2 in contact2.phone:
                if phone1 and phone2 and phone1 == phone2:
                    return True
        return False

    def _merge_contacts(self, existing_contact: Contact, new_contact: Contact) -> Contact:
        """合并两个联系人

        Args:
            existing_contact: 已存在的联系人
            new_contact: 新的联系人

        Returns:
            合并后的联系人
        """
        # 合并电话号码
        for phone in new_contact.phone:
            if phone and phone not in existing_contact.phone:
                existing_contact.phone.append(phone)

        # 如果新联系人的姓名更完整，则使用新联系人的姓名
        if len(new_contact.name) > len(existing_contact.name):
            existing_contact.name = new_contact.name

        # 合并其他信息
        if not existing_contact.email and new_contact.email:
            existing_contact.email = new_contact.email
        if not existing_contact.group and new_contact.group:
            existing_contact.group = new_contact.group
        if not existing_contact.notes and new_contact.notes:
            existing_contact.notes = new_contact.notes

        return existing_contact


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

        # 用于跟踪已处理的联系人，避免重复
        processed_contacts: List[Contact] = []
        contact_map: Dict[str, Contact] = {}  # 用于通过标准化电话号码快速查找联系人

        # 处理查询结果
        for i, result in enumerate(results):
            # 直接使用display_name字段作为姓名
            name = ''

            # 查找包含sort_key的键，正确处理"数字 sort_key"格式
            for key in result.keys():
                self.logger.debug(f"检查键: '{key}'")
                if 'sort_key' in key and result[key]:

                    name = self.process_value(result, key)
                    self.logger.debug(f"找到sort_key字段: key='{key}', value='{result[key]}'")
                    break

            phone = result.get('data1', '')

            # 如果没有找到sort_key或提取的姓名为空，尝试display_name_alt
            if not name:
                for key in result.keys():
                    self.logger.debug(f"检查alt键: '{key}'")
                    if 'display_name_alt' in key and result[key]:
                        name = result[key]
                        self.logger.debug(f"找到备选姓名字段: key='{key}', value='{result[key]}'")
                        break

            # 创建联系人对象
            contact = Contact(
                name=name if name else '未知姓名',
                phone=phone,  # data1字段存储电话号码
                email='',  # 在这个查询中不包含邮箱
                group=result.get('group_name', ''),
                notes=''
            )

            # 标准化电话号码用于比较
            normalized_phone = self._normalize_phone(phone)

            # 检查是否已存在相同电话号码的联系人，如果存在则合并
            if normalized_phone and normalized_phone in contact_map:
                existing_contact = contact_map[normalized_phone]
                # 如果新联系人的姓名更完整，则更新姓名
                if len(contact.name) > len(existing_contact.name) and contact.name != '未知姓名':
                    existing_contact.name = contact.name
                # 确保电话号码在列表中
                if phone and phone not in existing_contact.phone:
                    existing_contact.phone.append(phone)
            else:
                # 添加新联系人
                processed_contacts.append(contact)
                if normalized_phone:
                    contact_map[normalized_phone] = contact

        self.logger.info(f"处理后得到 {len(processed_contacts)} 个联系人对象")

        return processed_contacts
    import re

    def is_chinese(self, text):
        # 检查是否包含中文字符（\u4e00-\u9fff 是 CJK 统一汉字）
        return any(re.search(r'[\u4e00-\u9fff]', word) for word in text.split())

    def process_value(self, result, key):
        sort_key_value = result[key]

        if self.is_chinese(sort_key_value):
            name = self.extract_even_positions(sort_key_value)
        else:
            name = sort_key_value

        return name

    def extract_even_positions(self, text):
        words = text.split()
        selected = words[1::2]  # 提取第 2、4、6... 个词

        if len(selected) == 2:
            return ' '.join(selected)
        else:
            return ''.join(selected)

