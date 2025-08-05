import os
from typing import List, Optional, Dict, Any
from PIL import Image
import json

class DataProcessor:
    def __init__(self, cache_dir: Optional[str] = None):
        """初始化数据处理器
        
        Args:
            cache_dir: 缓存目录路径，如果为None则使用临时目录
        """
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def process_image(self, image_path: str) -> Optional[Image.Image]:
        """处理图像文件
        
        Args:
            image_path: 图像文件路径
        
        Returns:
            处理后的PIL Image对象，如果处理失败则返回None
        """
        try:
            # 打开并处理图像
            with Image.open(image_path) as img:
                # 转换为RGB模式（去除alpha通道）
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[3])
                    else:
                        background.paste(img, mask=img.split()[1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                return img
        except Exception as e:
            print(f"Error processing image {image_path}: {str(e)}")
            return None
    
    def save_processed_image(self, image: Image.Image, output_path: str,
                           format: str = 'JPEG', **kwargs) -> bool:
        """保存处理后的图像
        
        Args:
            image: PIL Image对象
            output_path: 输出文件路径
            format: 图像格式
            **kwargs: 保存参数
        
        Returns:
            是否保存成功
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path, format=format, **kwargs)
            return True
        except Exception as e:
            print(f"Error saving image to {output_path}: {str(e)}")
            return False
    
    def process_json_data(self, json_data: str) -> Optional[Dict[str, Any]]:
        """处理JSON数据
        
        Args:
            json_data: JSON字符串
        
        Returns:
            解析后的数据字典，如果解析失败则返回None
        """
        try:
            data = json.loads(json_data)
            return data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON data: {str(e)}")
            return None
    
    def save_processed_data(self, data: Dict[str, Any], output_path: str) -> bool:
        """保存处理后的数据
        
        Args:
            data: 要保存的数据字典
            output_path: 输出文件路径
        
        Returns:
            是否保存成功
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data to {output_path}: {str(e)}")
            return False
    
    def clean_cache(self) -> bool:
        """清理缓存目录
        
        Returns:
            是否清理成功
        """
        try:
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    os.remove(os.path.join(root, file))
            return True
        except Exception as e:
            print(f"Error cleaning cache: {str(e)}")
            return False
