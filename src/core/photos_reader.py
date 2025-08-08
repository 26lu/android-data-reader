# src/core/photos_reader.py

from typing import List, Optional, Dict, Any, Tuple
import os
import json
import shutil
import logging
from datetime import datetime
from PIL import Image

from .device_manager import DeviceManager
from .logger import default_logger

class PhotoInfo:
    def __init__(self, path: str, date: int, width: int = 0, height: int = 0,
                 size: int = 0, type: str = ''):
        self.path = path
        self.date = date  # 时间戳，单位毫秒
        self.width = width
        self.height = height
        self.size = size
        self.type = type

    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'date': self.date,
            'width': self.width,
            'height': self.height,
            'size': self.size,
            'type': self.type,
            'datetime': datetime.fromtimestamp(self.date / 1000).isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhotoInfo':
        return cls(
            path=data['path'],
            date=data['date'],
            width=data.get('width', 0),
            height=data.get('height', 0),
            size=data.get('size', 0),
            type=data.get('type', '')
        )

class PhotosReader:
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self.logger = default_logger or logging.getLogger(__name__)
        # 使用绝对路径确保临时目录可以被正确清理
        self.thumbnail_dir = os.path.abspath('thumbnails')
        if not os.path.exists(self.thumbnail_dir):
            os.makedirs(self.thumbnail_dir)

    def scan_photos(self, device_id=None) -> List[PhotoInfo]:
        if not device_id:
            devices = self.device_manager.get_devices()
            if not devices:
                self.logger.error("没有连接的设备")
                return []
            device_id = devices[0]

        permissions = self.device_manager.get_device_permissions(device_id)
        if not permissions.get('存储权限', False):
            self.logger.error("没有读取存储权限")
            return []

        photos = []
        for dir_path in ['/sdcard/DCIM', '/sdcard/Pictures']:
            try:
                command = ['shell', 'find', dir_path, '-type', 'f',
                           '-name', '*.jpg', '-o', '-name', '*.jpeg',
                           '-o', '-name', '*.png', '-o', '-name', '*.gif']
                success, output = self.device_manager._run_adb_command(command, device_id)
                if success:
                    for path in output.splitlines():
                        path = path.strip()
                        if path:
                            photo_info = self._get_photo_info(path, device_id)
                            if photo_info:
                                photos.append(photo_info)
            except Exception as e:
                self.logger.error(f"扫描照片时出错: {str(e)}")
                # 继续处理其他目录，不中断整个过程
                continue
        return sorted(photos, key=lambda x: x.date, reverse=True)

    def _get_photo_info(self, path: str, device_id: str) -> Optional[PhotoInfo]:
        try:
            timestamp_ms = int(datetime.now().timestamp() * 1000)
            return PhotoInfo(
                path=path,
                date=timestamp_ms,
                width=0,
                height=0,
                size=0,
                type=os.path.splitext(path)[1].lstrip('.').lower()
            )
        except Exception as e:
            self.logger.error(f"获取照片信息失败: {e}")
            return None

    def download_photo(self, photo_info: PhotoInfo, output_dir: str,
                       device_id: Optional[str] = None) -> Optional[str]:
        if not device_id:
            devices = self.device_manager.get_devices()
            if not devices:
                self.logger.error("没有连接的设备")
                return None
            device_id = devices[0]

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, os.path.basename(photo_info.path))
        args = ['pull', photo_info.path, output_path]
        success, _ = self.device_manager._run_adb_command(args, device_id)
        if success:
            return output_path
        else:
            self.logger.error(f"下载照片失败: {photo_info.path}")
            return None

    def create_thumbnail(self, photo_path: str, size: Tuple[int, int] = (200, 200),
                         output_dir: Optional[str] = None) -> Optional[str]:
        if output_dir is None:
            output_dir = self.thumbnail_dir

        os.makedirs(output_dir, exist_ok=True)

        try:
            with Image.open(photo_path) as img:
                img.thumbnail(size)
                thumbnail_path = os.path.join(
                    output_dir,
                    f"thumb_{os.path.basename(photo_path)}"
                )
                img.save(thumbnail_path)
                return thumbnail_path
        except Exception as e:
            self.logger.error(f"创建缩略图失败: {str(e)}")
            return None

    def save_photo_info(self, photos: List[PhotoInfo], output_path: str):
        data = [photo.to_dict() for photo in photos]
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_photo_info(self, input_path: str) -> List[PhotoInfo]:
        if not os.path.exists(input_path):
            return []
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [PhotoInfo.from_dict(item) for item in data]
        except Exception as e:
            self.logger.error(f"加载照片信息失败: {str(e)}")
            return []

    def cleanup_cache(self):
        try:
            if os.path.exists(self.thumbnail_dir):
                shutil.rmtree(self.thumbnail_dir)
            os.makedirs(self.thumbnail_dir)
        except Exception as e:
            self.logger.error(f"清理缓存目录失败: {str(e)}")
