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
        
    def create_thumbnail(self, photo_path: str, output_dir: Optional[str] = None, 
                        size: Tuple[int, int] = (200, 200)) -> Optional[str]:
        """为照片创建缩略图
        
        Args:
            photo_path: 照片路径
            output_dir: 输出目录，默认为缓存目录
            size: 缩略图大小，默认200x200
            
        Returns:
            缩略图路径，失败时返回None
        """
        self.logger.debug(f"为照片创建缩略图: {photo_path}")
        
        if not os.path.exists(photo_path):
            self.logger.error(f"照片文件不存在: {photo_path}")
            return None
            
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
                self.logger.debug(f"缩略图创建成功: {thumbnail_path}")
                return thumbnail_path
        except FileNotFoundError:
            self.logger.error(f"照片文件未找到: {photo_path}")
            return None
        except OSError as e:
            self.logger.error(f"处理图像文件时出错: {photo_path}, 错误: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"创建缩略图时出现未预期错误: {photo_path}, 错误: {str(e)}")
            return None
            
    def save_photo_info(self, photos: List[PhotoInfo], output_path: str):
        """保存照片信息到文件
        
        Args:
            photos: 照片信息列表
            output_path: 输出文件路径
        """
        self.logger.info(f"开始保存 {len(photos)} 条照片信息到 {output_path}")
        
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
            data = [photo.to_dict() for photo in photos]
            
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            self.logger.debug(f"创建目录: {os.path.dirname(output_path)}")
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"成功保存 {len(photos)} 条照片信息到 {output_path}")
        except OSError as e:
            self.logger.error(f"保存照片信息到文件时出错: {str(e)}")
            raise IOError(f"保存照片信息失败: {str(e)}")
        except json.JSONEncodeError as e:
            self.logger.error(f"序列化照片信息时出错: {str(e)}")
            raise ValueError(f"照片信息序列化失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"保存照片信息时出现未预期错误: {str(e)}")
            raise RuntimeError(f"保存照片信息时出错: {str(e)}")
            
    def load_photo_info(self, input_path: str) -> List[PhotoInfo]:
        """从文件加载照片信息
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            照片信息列表
        """
        self.logger.info(f"开始从 {input_path} 加载照片信息")
        
        # 输入验证
        if not input_path:
            self.logger.error("输入路径不能为空")
            return []
            
        if not os.path.exists(input_path):
            self.logger.warning(f"照片信息文件不存在: {input_path}")
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
            photos = [PhotoInfo.from_dict(item) for item in data]
            self.logger.info(f"成功加载 {len(photos)} 条照片信息")
            return photos
        except json.JSONDecodeError as e:
            self.logger.error(f"解析照片信息文件失败: {str(e)}")
            return []
        except OSError as e:
            self.logger.error(f"读取照片信息文件时出错: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"加载照片信息时出现未预期错误: {str(e)}")
            return []
            
    def cleanup_cache(self):
        """清理缓存目录"""
        self.logger.info("开始清理缓存目录")
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                self.logger.debug(f"删除缓存目录: {self.cache_dir}")
            os.makedirs(self.cache_dir)
            self.logger.debug(f"重新创建缓存目录: {self.cache_dir}")
            self.logger.info("缓存目录清理完成")
        except OSError as e:
            self.logger.error(f"清理缓存目录时出现文件系统错误: {str(e)}")
        except Exception as e:
            self.logger.error(f"清理缓存目录时出现未预期错误: {str(e)}")
