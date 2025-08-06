import subprocess
import json
import logging
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from .device_manager import DeviceManager
from .logger import default_logger
import re
from collections import defaultdict

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
        """获取所有联系人，包括姓名、电话、邮箱、分组、备注"""

        if not device_id:
            devices = self.device_manager.get_devices()
            if not devices:
                self.logger.error("没有连接的设备")
                return []
            device_id = devices[0]

        # 检查权限
        permissions = self.device_manager.get_device_permissions(device_id)
        if not permissions.get('android.permission.READ_CONTACTS', False):
            if 'unauthorized' in str(permissions.get('error', '')).lower():
                self.logger.error("设备未授权，请在手机上确认USB调试授权")
            else:
                self.logger.error("没有读取通讯录权限")
            return []

        # 获取 group_id → group_name 映射
        group_map = {}
        try:
            group_result = self._run_query("content://com.android.contacts/groups", device_id)
            for row in group_result:
                group_id = row.get('_id')
                group_name = row.get('title')
                if group_id and group_name:
                    group_map[group_id] = group_name
        except Exception as e:
            self.logger.warning(f"无法读取分组信息: {str(e)}")

        # 查询 data 表（包含电话、邮箱、分组、备注等）
        query = "content://com.android.contacts/data"
        results = self._run_query(query, device_id)
        self.logger.info(f"从设备 {device_id} 获取到 {len(results)} 条原始联系人数据")

        # 用姓名作为key，存储联系人对象
        contact_map = {}

        for row in results:
            mimetype = row.get('mimetype', '')
            data1 = row.get('data1', '')
            if not data1:
                continue

            # 尝试获取姓名，优先级 sort_key > display_name > display_name_alt
            name = ''
            for k in ['sort_key', 'display_name', 'display_name_alt']:
                if k in row and row[k]:
                    name = self.process_value(row, k)
                    break

            if not name:
                # 没有姓名的忽略
                continue

            # 如果该姓名已经存在，获取已存联系人，否则新建
            if name in contact_map:
                contact = contact_map[name]
            else:
                contact = Contact(name=name)
                contact_map[name] = contact

            # 根据mimetype填充对应字段，合并时避免重复添加
            if mimetype == 'vnd.android.cursor.item/phone_v2':
                normalized = self._normalize_phone(data1)
                if normalized and normalized not in contact.phone:
                    contact.phone.append(normalized)

            elif mimetype == 'vnd.android.cursor.item/email_v2':
                if data1 not in contact.email:
                    contact.email.append(data1)

            elif mimetype == 'vnd.android.cursor.item/group_membership':
                group_id = data1
                group_name = group_map.get(group_id, '')
                if group_name and group_name not in contact.group:
                    if contact.group:
                        contact.group += ", " + group_name
                    else:
                        contact.group = group_name

            elif mimetype == 'vnd.android.cursor.item/note':
                # 合并备注：如果已有备注且不重复，追加；否则直接赋值
                if contact.notes:
                    if data1 not in contact.notes:
                        contact.notes += " | " + data1
                else:
                    contact.notes = data1

        final_contacts = list(contact_map.values())
        self.logger.info(f"成功构建 {len(final_contacts)} 个合并后的联系人对象")
        return final_contacts

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
