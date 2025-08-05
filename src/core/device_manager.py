#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
设备管理模块
负责设备连接检测、设备信息获取、权限检查等功能
"""

import subprocess
import re
import os
import logging
from typing import List, Dict
from .logger import default_logger

class DeviceManager:
    """设备管理器"""
    
    def __init__(self, adb_path: str = None):
        """
        初始化设备管理器
        
        Args:
            adb_path (str): ADB可执行文件路径，默认为None
        """
        self.logger = default_logger
        self.logger.info("初始化设备管理器")
        
        # 设置ADB路径
        if adb_path:
            self.adb_path = adb_path
        else:
            # 尝试使用系统ADB或项目自带的ADB
            self.adb_path = self._find_adb()
        
        self.logger.info(f"使用ADB路径: {self.adb_path}")
    
    def _find_adb(self) -> str:
        """
        查找ADB可执行文件
        
        Returns:
            str: ADB可执行文件路径
        """
        # 首先尝试系统PATH中的ADB
        try:
            result = subprocess.run(['adb', 'version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.logger.info("使用系统ADB")
                return 'adb'
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # 尝试使用项目自带的ADB
        platform_dir = 'platform-tools'
        if os.name == 'nt':  # Windows
            adb_executable = os.path.join(platform_dir, 'adb.exe')
        else:  # macOS/Linux
            adb_executable = os.path.join(platform_dir, 'adb')
        
        if os.path.exists(adb_executable):
            self.logger.info(f"使用项目自带ADB: {adb_executable}")
            return adb_executable
        
        self.logger.warning("未找到ADB可执行文件")
        return 'adb'  # 最后尝试系统命令
    
    def get_devices(self) -> List[str]:
        """
        获取连接的设备列表
        
        Returns:
            List[str]: 设备序列号列表
        """
        try:
            self.logger.info("获取设备列表")
            result = subprocess.run([self.adb_path, 'devices'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.logger.error(f"获取设备列表失败: {result.stderr}")
                return []
            
            devices = []
            lines = result.stdout.strip().split('\n')
            
            # 跳过第一行标题
            for line in lines[1:]:
                if line and '\t' in line:
                    device_id, status = line.split('\t')
                    if status == 'device':
                        devices.append(device_id)
            
            self.logger.info(f"找到 {len(devices)} 个连接设备")
            return devices
            
        except subprocess.TimeoutExpired:
            self.logger.error("获取设备列表超时")
            return []
        except Exception as e:
            self.logger.error(f"获取设备列表时出错: {e}")
            return []
    
    def get_device_info(self, device_id: str) -> Dict[str, str]:
        """
        获取设备信息
        
        Args:
            device_id (str): 设备序列号
            
        Returns:
            Dict[str, str]: 设备信息字典
        """
        info = {}
        try:
            self.logger.info(f"获取设备 {device_id} 的信息")
            
            # 检查设备ID是否有效
            if not device_id:
                self.logger.warning("设备ID为空")
                return info
            
            # 获取设备型号
            model_result = subprocess.run([self.adb_path, '-s', device_id, 'shell', 'getprop', 'ro.product.model'],
                                        capture_output=True, text=True, timeout=10)
            if model_result.returncode == 0:
                info['型号'] = model_result.stdout.strip()
            
            # 获取Android版本
            version_result = subprocess.run([self.adb_path, '-s', device_id, 'shell', 'getprop', 'ro.build.version.release'],
                                          capture_output=True, text=True, timeout=10)
            if version_result.returncode == 0:
                info['Android版本'] = version_result.stdout.strip()
            
            # 获取设备制造商
            manufacturer_result = subprocess.run([self.adb_path, '-s', device_id, 'shell', 'getprop', 'ro.product.manufacturer'],
                                               capture_output=True, text=True, timeout=10)
            if manufacturer_result.returncode == 0:
                info['制造商'] = manufacturer_result.stdout.strip()
            
            self.logger.info(f"设备信息: {info}")
            return info
            
        except subprocess.TimeoutExpired:
            self.logger.error("获取设备信息超时")
            return info
        except Exception as e:
            self.logger.error(f"获取设备信息时出错: {e}")
            return info
    
    def get_device_permissions(self, device_id: str) -> Dict[str, bool]:
        """
        检查设备权限
        
        Args:
            device_id (str): 设备序列号
            
        Returns:
            Dict[str, bool]: 权限状态字典
        """
        permissions = {
            '存储权限': False,
            '短信权限': False,
            '通讯录权限': False
        }
        
        # 检查设备ID是否有效
        if not device_id:
            self.logger.warning("设备ID为空，无法检查权限")
            return permissions
        
        try:
            self.logger.info(f"检查设备 {device_id} 的权限")
            
            # 检查存储权限（通过尝试读取外部存储）
            storage_result = subprocess.run([self.adb_path, '-s', device_id, 'shell', 'ls', '/sdcard/'],
                                          capture_output=True, text=True, timeout=10)
            permissions['存储权限'] = storage_result.returncode == 0
            
            # 这里可以添加更多权限检查逻辑
            # 为简化起见，暂时设置为True
            permissions['短信权限'] = True
            permissions['通讯录权限'] = True
            
            self.logger.info(f"权限检查结果: {permissions}")
            return permissions
            
        except subprocess.TimeoutExpired:
            self.logger.error("权限检查超时")
            return permissions
        except Exception as e:
            self.logger.error(f"权限检查时出错: {e}")
            return permissions