import os
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from .device_manager import DeviceManager  # 确保此模块存在并正确导入


@dataclass
class SMSMessage:
    address: str
    body: str
    date: int  # 毫秒时间戳
    type: int

    @property
    def datetime_str(self) -> str:
        return datetime.fromtimestamp(self.date / 1000).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def time(self) -> str:
        """兼容旧代码"""
        return self.datetime_str

    @property
    def content(self) -> str:
        """兼容旧字段 'content'，实际返回 body"""
        return self.body

    def to_dict(self) -> Dict[str, Any]:
        return {
            'address': self.address,
            'body': self.body,
            'date': self.date,
            'type': self.type,
            'datetime': datetime.fromtimestamp(self.date / 1000).isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SMSMessage':
        return cls(
            address=data['address'],
            body=data['body'],
            date=data['date'],
            type=data['type']
        )


class SMSReader:
    def __init__(self, device_manager: DeviceManager, logger=None):
        self.device_manager = device_manager
        self.logger = logger or logging.getLogger(__name__)

        # 配置日志（如果没有配置过）
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

    def _run_query(self, query: str, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        device_id = device_id or ''
        cmd_args = ['shell', 'content', 'query', '--uri', query]

        success, output = self.device_manager._run_adb_command(cmd_args, device_id if device_id else "")

        if not success:
            self.logger.error(f"查询失败: {output}")
            return []

        return self._parse_query_result(output)

    def _parse_query_result(self, result: str) -> List[Dict[str, str]]:
        results = []
        lines = result.strip().split('\n')
        self.logger.debug(f"解析 {len(lines)} 行查询结果")

        for line in lines:
            if line.startswith('Row:'):
                try:
                    parts = line.split('Row:')[1].strip().split(',')
                    row_data = {}
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            row_data[key.strip()] = value.strip()
                    results.append(row_data)
                except (ValueError, IndexError) as e:
                    self.logger.error(f"解析行失败: {line}, 错误: {str(e)}", exc_info=True)
                except Exception as e:
                    self.logger.error(f"解析行时出现未预期错误: {line}, 错误: {str(e)}", exc_info=True)

        self.logger.debug(f"成功解析 {len(results)} 行数据")
        return results

    def get_all_sms(self, device_id: Optional[str] = None) -> List[SMSMessage]:
        if not device_id:
            devices = self.device_manager.get_devices()
            if not devices:
                self.logger.error("没有连接的设备")
                return []
            device_id = devices[0]

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
                self.logger.error(f"解析短信数据失败: {str(e)}", exc_info=True)

        return messages

    def get_conversations(self, device_id: Optional[str] = None) -> Dict[str, List[SMSMessage]]:
        all_sms = self.get_all_sms(device_id)
        conversations = {}

        for sms in all_sms:
            conversations.setdefault(sms.address, []).append(sms)

        for number in conversations:
            conversations[number].sort(key=lambda x: x.date)

        return conversations

    def search_sms(self, keyword: str, device_id: Optional[str] = None) -> List[SMSMessage]:
        all_sms = self.get_all_sms(device_id)
        keyword = keyword.lower()

        return [
            sms for sms in all_sms
            if keyword in sms.body.lower() or keyword in sms.address.lower()
        ]

    def get_sms_by_date_range(self, start_date: datetime, end_date: datetime,
                             device_id: Optional[str] = None) -> List[SMSMessage]:
        all_sms = self.get_all_sms(device_id)
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        return [
            sms for sms in all_sms
            if start_ts <= sms.date <= end_ts
        ]

    def save_sms(self, messages: List[SMSMessage], output_path: str):
        self.logger.info(f"开始保存 {len(messages)} 条短信数据到 {output_path}")

        if not output_path:
            self.logger.error("保存失败：输出路径不能为空")
            raise ValueError("输出路径不能为空")

        try:
            abs_output_path = os.path.abspath(output_path)
            abs_cwd = os.path.abspath(os.getcwd())
            common_path = os.path.commonpath([abs_output_path, abs_cwd])
            if common_path != abs_cwd:
                err_msg = f"输出路径必须在当前工作目录 {abs_cwd} 内，但传入路径为 {abs_output_path}"
                self.logger.error(err_msg)
                raise ValueError(err_msg)
        except Exception as e:
            self.logger.error(f"输出路径验证失败: {e}", exc_info=True)
            raise ValueError(f"输出路径验证失败: {e}")

        try:
            dir_name = os.path.dirname(abs_output_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)

            data = [sms.to_dict() for sms in messages]
            with open(abs_output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"短信数据成功保存到 {abs_output_path}")

        except Exception as e:
            self.logger.error(f"保存短信数据时出错: {e}", exc_info=True)
            raise RuntimeError(f"保存短信数据时出错: {e}")

    def load_sms(self, input_path: str) -> List[SMSMessage]:
        if not input_path:
            self.logger.warning("加载失败：输入路径为空")
            return []

        if not os.path.exists(input_path):
            self.logger.warning(f"加载失败：文件不存在，路径 {input_path}")
            return []

        try:
            abs_input_path = os.path.abspath(input_path)
            abs_cwd = os.path.abspath(os.getcwd())
            common_path = os.path.commonpath([abs_input_path, abs_cwd])
            if common_path != abs_cwd:
                self.logger.warning(f"输入路径 {abs_input_path} 不在当前工作目录 {abs_cwd} 内")
                return []
        except Exception as e:
            self.logger.error(f"输入路径验证失败: {e}", exc_info=True)
            return []

        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"成功加载短信数据，共 {len(data)} 条")
            return [SMSMessage.from_dict(item) for item in data]
        except Exception as e:
            self.logger.error(f"加载短信数据失败: {e}", exc_info=True)
            return []
