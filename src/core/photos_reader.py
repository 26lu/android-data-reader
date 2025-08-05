from typing import List, Dict, Optional, Any, Tuple
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from PIL import Image
import shutil
from .device_manager import DeviceManager
from .logger import default_logger

class PhotoInfo:
    def __init__(self, path: str, date: int, width: int = 0, height: int = 0,
                 size: int = 0, type: str = ''):
        """初始化照片信息对象
        
        Args:
            path: 设备上的文件路径
            date: 创建时间戳(毫秒)
            width: 图片宽度
            height: 图片高度
            size: 文件大小(字节)
            type: 文件类型
        """
        self.path = path
        self.date = date
        self.width = width
        self.height = height
        self.size = size
        self.type = type
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
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
        """从字典创建照片信息对象"""
        return cls(
            path=data['path'],
            date=data['date'],
            width=data['width'],
            height=data['height'],
            size=data['size'],
            type=data['type']
        )

class PhotosReader:
    def __init__(self, device_manager):
        self.device_manager = device_manager
        self.logger = default_logger
        # 创建缩略图目录
        self.thumbnail_dir = 'thumbnails'
        if not os.path.exists(self.thumbnail_dir):
            os.makedirs(self.thumbnail_dir)
    
    def scan_photos(self, device_id=None):
        """扫描照片"""
        if not device_id:
            devices = self.device_manager.get_devices()
            if not devices:
                self.logger.error("没有连接的设备")
                return []
            device_id = devices[0]
            
        # 检查权限
        permissions = self.device_manager.get_device_permissions(device_id)
        if not permissions.get('存储权限', False):
            self.logger.error("没有读取存储权限")
            return []
            
        device_arg = ['-s', device_id] if device_id else []
        
        # 扫描DCIM和Pictures目录
        photos = []
        for dir_path in ['/sdcard/DCIM', '/sdcard/Pictures']:
            success, output = self.device_manager._run_adb_command(
                device_arg + ['shell', 'find', dir_path, '-type', 'f', 
                            '-name', '*.jpg', '-o', '-name', '*.jpeg', 
                            '-o', '-name', '*.png', '-o', '-name', '*.gif']
            )
            
            if success:
                for path in output.splitlines():
                    path = path.strip()
                    if path:
                        photo_info = self._get_photo_info(path, device_id)
                        if photo_info:
                            photos.append(photo_info)
                            
        return sorted(photos, key=lambda x: x.date, reverse=True)
        
    def get_photo_by_date(self, start_date: datetime, end_date: datetime,
                         device_id: Optional[str] = None) -> List[PhotoInfo]:
        """获取指定时间范围内的照片
        
        Args:
            start_date: 开始时间
            end_date: 结束时间
            device_id: 设备ID
            
        Returns:
            时间范围内的照片列表
        """
        all_photos = self.scan_photos(device_id)
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        return [
            photo for photo in all_photos
            if start_ts <= photo.date <= end_ts
        ]
        
    def download_photo(self, photo_info: PhotoInfo, output_dir: str,
                      device_id: Optional[str] = None) -> Optional[str]:
        """下载照片到本地
        
        Args:
            photo_info: 照片信息对象
            output_dir: 输出目录
            device_id: 设备ID
            
        Returns:
            本地文件路径,如果下载失败则返回None
        """
        device_arg = ['-s', device_id] if device_id else []
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, os.path.basename(photo_info.path))
        success = self.device_manager._run_adb_command(
            device_arg + ['pull', photo_info.path, output_path]
        )[0]
        
        return output_path if success else None
        
    def create_thumbnail(self, photo_path: str, size: Tuple[int, int] = (200, 200),
                        output_dir: str = None) -> Optional[str]:
        """创建缩略图
        
        Args:
            photo_path: 照片文件路径
            size: 缩略图大小(宽,高)
            output_dir: 输出目录,如果为None则使用cache_dir
            
        Returns:
            缩略图路径,如果创建失败则返回None
        """
        if output_dir is None:
            output_dir = self.cache_dir
            
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
        """保存照片信息到文件
        
        Args:
            photos: 照片信息列表
            output_path: 输出文件路径
        """
        data = [photo.to_dict() for photo in photos]
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def load_photo_info(self, input_path: str) -> List[PhotoInfo]:
        """从文件加载照片信息
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            照片信息列表
        """
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
        """清理缓存目录"""
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir)
        except Exception as e:
            self.logger.error(f"清理缓存目录失败: {str(e)}")
