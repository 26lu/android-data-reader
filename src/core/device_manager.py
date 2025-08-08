#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
设备管理模块
负责设备连接检测、设备信息获取、权限检查等功能
"""

import subprocess
import re
import os
import sys
import logging
from typing import List, Dict, Tuple, Optional
from .logger import default_logger

class DeviceManager:
    """设备管理器"""
    
    def __init__(self, adb_path: str = None):
        """
        初始化设备管理器
        
        Args:
            adb_path: ADB可执行文件路径，如果为None则自动查找
        """
        self.logger = default_logger
        self.logger.info("初始化设备管理器")
        
        if adb_path:
            self.adb_path = adb_path
        else:
            self.adb_path = self._find_adb()
            
        self.logger.info(f"使用ADB路径: {self.adb_path}")

    def _find_adb(self) -> str:
        """查找ADB可执行文件路径
        
        Returns:
            ADB可执行文件路径
        """
        self.logger.debug("正在查找ADB路径")
        
        # 首先尝试使用系统ADB
        try:
            # 在Windows上运行adb.exe时添加CREATE_NO_WINDOW标志以避免控制台窗口闪烁
            if sys.platform == "win32":
                # Windows平台，添加CREATE_NO_WINDOW标志
                creation_flags = subprocess.CREATE_NO_WINDOW
            else:
                creation_flags = 0
                
            result = subprocess.run(['adb', 'version'], 
                                  capture_output=True, text=True, timeout=5,
                                  creationflags=creation_flags)
            if result.returncode == 0:
                self.logger.info("使用系统ADB")
                return 'adb'
        except (subprocess.SubprocessError, FileNotFoundError):
            self.logger.debug("系统ADB不可用")
            pass
        except subprocess.TimeoutExpired:
            self.logger.warning("系统ADB版本检查超时")
            pass
        
        # 尝试使用项目自带的ADB
        # 处理打包后的可执行文件路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe文件运行
            base_path = sys._MEIPASS
            platform_dir = os.path.join(base_path, 'platform-tools')
            
            if sys.platform == 'win32':
                adb_executable = os.path.join(platform_dir, 'adb.exe')
            else:
                adb_executable = os.path.join(platform_dir, 'adb')
                
            if os.path.exists(adb_executable):
                self.logger.info(f"使用项目自带ADB: {adb_executable}")
                return adb_executable
        elif os.path.exists('platform-tools'):
            # 如果是直接运行Python脚本
            platform_dir = 'platform-tools'
            if sys.platform == 'win32':
                adb_executable = os.path.join(platform_dir, 'adb.exe')
            else:
                adb_executable = os.path.join(platform_dir, 'adb')
                
            if os.path.exists(adb_executable):
                self.logger.info(f"使用项目自带ADB: {adb_executable}")
                return adb_executable
            
        self.logger.error("未找到可用的ADB")
        raise FileNotFoundError("未找到可用的ADB可执行文件")
        
    def _run_adb_command(self, args: List[str], device_id: Optional[str] = None, 
                        timeout: int = 30) -> Tuple[bool, str]:
        """运行ADB命令"""
        try:
            # 构建完整参数
            full_args = []
            if device_id:
                full_args.extend(['-s', device_id])
            full_args.extend(args)
            
            self.logger.debug(f"执行ADB命令: {self.adb_path} {' '.join(full_args)}")
            
            # 在Windows上运行adb.exe时添加CREATE_NO_WINDOW标志以避免控制台窗口闪烁
            if sys.platform == "win32" and self.adb_path.endswith('.exe'):
                # Windows平台且是exe文件，添加CREATE_NO_WINDOW标志
                creation_flags = subprocess.CREATE_NO_WINDOW
            else:
                creation_flags = 0
                
            result = subprocess.run(
                [self.adb_path] + full_args,
                capture_output=True, 
                text=True, 
                timeout=timeout,
                encoding='utf-8',
                creationflags=creation_flags  # 添加此参数以避免控制台窗口闪烁
            )
            
            self.logger.debug(f"ADB命令返回码: {result.returncode}")
            self.logger.debug(f"ADB命令stdout长度: {len(result.stdout)}")
            self.logger.debug(f"ADB命令stderr长度: {len(result.stderr)}")
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                error_msg = result.stderr.strip()
                self.logger.warning(f"ADB命令执行失败: {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"ADB命令执行超时: {self.adb_path} {' '.join(full_args)}")
            return False, "命令执行超时"
        except Exception as e:
            self.logger.error(f"执行ADB命令时发生未知错误: {str(e)}")
            return False, f"执行命令时发生错误: {str(e)}"
        
    def get_devices(self) -> List[str]:
        """获取连接的设备列表
        
        Returns:
            设备ID列表
        """
        self.logger.info("获取设备列表")
        try:
            # 在Windows上运行adb.exe时添加CREATE_NO_WINDOW标志以避免控制台窗口闪烁
            if sys.platform == "win32" and self.adb_path.endswith('.exe'):
                # Windows平台且是exe文件，添加CREATE_NO_WINDOW标志
                creation_flags = subprocess.CREATE_NO_WINDOW
            else:
                creation_flags = 0
                
            self.logger.debug(f"执行命令: {self.adb_path} devices")
            result = subprocess.run([self.adb_path, 'devices'], 
                                  capture_output=True, text=True, timeout=10,
                                  creationflags=creation_flags)
            
            if result.returncode != 0:
                self.logger.error(f"获取设备列表失败: {result.stderr}")
                return []
            
            devices = []
            lines = result.stdout.strip().split('\n')
            # 跳过第一行标题
            for line in lines[1:]:
                if line.strip() and not line.startswith('*'):
                    device_id = line.split()[0]
                    if device_id != 'List':
                        devices.append(device_id)
            
            self.logger.info(f"找到 {len(devices)} 个连接设备")
            self.logger.debug(f"设备列表: {devices}")
            
            # 如果没有找到设备，记录更多信息帮助诊断
            if not devices:
                self.logger.info("未找到设备，可能的原因：")
                self.logger.info("1. 未连接Android设备")
                self.logger.info("2. 未在设备上启用USB调试")
                self.logger.info("3. 未在设备上授权调试权限")
                self.logger.info("4. USB线缆仅支持充电不支持数据传输")
                self.logger.info("5. 设备驱动未正确安装")
                self.logger.info("6. USB连接模式不正确（应选择文件传输/MTP模式）")
                self.logger.info("故障排除建议：")
                self.logger.info("- 确保已在手机上启用'开发者选项'和'USB调试'")
                self.logger.info("- 重新连接USB线，确认手机上弹出的授权提示")
                self.logger.info("- 尝试更换USB线缆和端口")
                self.logger.info("- 安装手机品牌的官方USB驱动程序")
            
            return devices
        except Exception as e:
            self.logger.error(f"获取设备列表时出错: {str(e)}")
            return []
    
    def detect_mtp_devices(self) -> List[str]:
        """检测MTP模式下的设备（预留功能）
        
        Returns:
            MTP设备列表
        """
        self.logger.info("检测MTP设备（预留功能）")
        # TODO: 实现MTP设备检测
        # 这将允许在不启用USB调试的情况下检测设备
        # 但功能会受到限制，只能访问媒体文件
        return []
    
    def get_device_info(self, device_id: str) -> Dict[str, str]:
        """获取设备详细信息
        
        Args:
            device_id: 设备ID
            
        Returns:
            设备信息字典
        """
        self.logger.info(f"获取设备信息: {device_id}")
        info = {}
        
        try:
            # 在Windows上运行adb.exe时添加CREATE_NO_WINDOW标志以避免控制台窗口闪烁
            if sys.platform == "win32" and self.adb_path.endswith('.exe'):
                # Windows平台且是exe文件，添加CREATE_NO_WINDOW标志
                creation_flags = subprocess.CREATE_NO_WINDOW
            else:
                creation_flags = 0
                
            # 获取设备型号
            self.logger.debug(f"获取设备型号: {device_id}")
            model_result = subprocess.run([self.adb_path, '-s', device_id, 'shell', 'getprop', 'ro.product.model'],
                                        capture_output=True, text=True, timeout=10,
                                        creationflags=creation_flags)
            if model_result.returncode == 0:
                info['model'] = model_result.stdout.strip()
            else:
                self.logger.warning(f"获取设备型号失败: {model_result.stderr}")
                
            # 获取Android版本
            self.logger.debug(f"获取Android版本: {device_id}")
            version_result = subprocess.run([self.adb_path, '-s', device_id, 'shell', 'getprop', 'ro.build.version.release'],
                                          capture_output=True, text=True, timeout=10,
                                          creationflags=creation_flags)
            if version_result.returncode == 0:
                info['android_version'] = version_result.stdout.strip()
            else:
                self.logger.warning(f"获取Android版本失败: {version_result.stderr}")
                
            # 获取制造商
            self.logger.debug(f"获取制造商: {device_id}")
            manufacturer_result = subprocess.run([self.adb_path, '-s', device_id, 'shell', 'getprop', 'ro.product.manufacturer'],
                                               capture_output=True, text=True, timeout=10,
                                               creationflags=creation_flags)
            if manufacturer_result.returncode == 0:
                info['manufacturer'] = manufacturer_result.stdout.strip()
            else:
                self.logger.warning(f"获取制造商失败: {manufacturer_result.stderr}")
                
            return info
        except Exception as e:
            self.logger.error(f"获取设备信息时出错: {str(e)}")
            return info
            
    def get_device_permissions(self, device_id: str) -> Dict[str, bool]:
        """检查设备权限状态
        
        Args:
            device_id: 设备ID
            
        Returns:
            权限状态字典
        """
        self.logger.info(f"检查设备权限: {device_id}")
        permissions = {}
        
        try:
            # 在Windows上运行adb.exe时添加CREATE_NO_WINDOW标志以避免控制台窗口闪烁
            if sys.platform == "win32" and self.adb_path.endswith('.exe'):
                # Windows平台且是exe文件，添加CREATE_NO_WINDOW标志
                creation_flags = subprocess.CREATE_NO_WINDOW
            else:
                creation_flags = 0
                
            # 检查存储权限
            self.logger.debug(f"检查存储权限: {device_id}")
            storage_result = subprocess.run([self.adb_path, '-s', device_id, 'shell', 'ls', '/sdcard/'],
                                          capture_output=True, text=True, timeout=10,
                                          creationflags=creation_flags)
            permissions['存储权限'] = storage_result.returncode == 0
            if not permissions['存储权限']:
                self.logger.warning(f"存储权限检查失败: {storage_result.stderr}")
            
            # 检查ADB权限
            self.logger.debug(f"检查ADB调试权限: {device_id}")
            adb_result = subprocess.run([self.adb_path, '-s', device_id, 'shell', 'id'],
                                      capture_output=True, text=True, timeout=10,
                                      creationflags=creation_flags)
            permissions['ADB调试权限'] = adb_result.returncode == 0
            if not permissions['ADB调试权限']:
                self.logger.warning(f"ADB调试权限检查失败: {adb_result.stderr}")
                
            # 检查联系人读取权限
            self.logger.debug(f"检查联系人读取权限: {device_id}")
            contacts_result = subprocess.run(
                [self.adb_path, '-s', device_id, 'shell', 'content', 'query', '--uri', 'content://com.android.contacts/data/phones', '--limit', '1'],
                capture_output=True, text=True, timeout=10,
                creationflags=creation_flags
            )
            permissions['android.permission.READ_CONTACTS'] = contacts_result.returncode == 0
            if not permissions['android.permission.READ_CONTACTS']:
                self.logger.warning(f"联系人读取权限检查失败: {contacts_result.stderr}")
            
            # 检查短信读取权限
            self.logger.debug(f"检查短信读取权限: {device_id}")
            sms_result = subprocess.run(
                [self.adb_path, '-s', device_id, 'shell', 'content', 'query', '--uri', 'content://sms', '--limit', '1'],
                capture_output=True, text=True, timeout=10,
                creationflags=creation_flags
            )
            permissions['android.permission.READ_SMS'] = sms_result.returncode == 0
            if not permissions['android.permission.READ_SMS']:
                self.logger.warning(f"短信读取权限检查失败: {sms_result.stderr}")
            
            return permissions
        except Exception as e:
            self.logger.error(f"检查设备权限时出错: {str(e)}")
            return permissions
            
    def check_permissions(self, device_id: str) -> Dict[str, bool]:
        """检查设备权限状态
        
        Args:
            device_id: 设备ID
            
        Returns:
            权限状态字典
        """
        self.logger.info(f"检查设备权限: {device_id}")
        permissions = {}
        
        try:
            # 在Windows上运行adb.exe时添加CREATE_NO_WINDOW标志以避免控制台窗口闪烁
            if sys.platform == "win32" and self.adb_path.endswith('.exe'):
                # Windows平台且是exe文件，添加CREATE_NO_WINDOW标志
                creation_flags = subprocess.CREATE_NO_WINDOW
            else:
                creation_flags = 0
                
            # 检查存储权限
            self.logger.debug(f"检查存储权限: {device_id}")
            storage_result = subprocess.run([self.adb_path, '-s', device_id, 'shell', 'ls', '/sdcard/'],
                                          capture_output=True, text=True, timeout=10,
                                          creationflags=creation_flags)
            permissions['存储权限'] = storage_result.returncode == 0
            if not permissions['存储权限']:
                self.logger.warning(f"存储权限检查失败: {storage_result.stderr}")
            
            # 检查ADB权限
            self.logger.debug(f"检查ADB调试权限: {device_id}")
            adb_result = subprocess.run([self.adb_path, '-s', device_id, 'shell', 'id'],
                                      capture_output=True, text=True, timeout=10,
                                      creationflags=creation_flags)
            permissions['ADB调试权限'] = adb_result.returncode == 0
            if not permissions['ADB调试权限']:
                self.logger.warning(f"ADB调试权限检查失败: {adb_result.stderr}")
                
            # 检查联系人读取权限
            self.logger.debug(f"检查联系人读取权限: {device_id}")
            contacts_result = subprocess.run(
                [self.adb_path, '-s', device_id, 'shell', 'content', 'query', '--uri', 'content://com.android.contacts/data/phones', '--limit', '1'],
                capture_output=True, text=True, timeout=10,
                creationflags=creation_flags
            )
            permissions['android.permission.READ_CONTACTS'] = contacts_result.returncode == 0
            if not permissions['android.permission.READ_CONTACTS']:
                self.logger.warning(f"联系人读取权限检查失败: {contacts_result.stderr}")
            
            # 检查短信读取权限
            self.logger.debug(f"检查短信读取权限: {device_id}")
            sms_result = subprocess.run(
                [self.adb_path, '-s', device_id, 'shell', 'content', 'query', '--uri', 'content://sms', '--limit', '1'],
                capture_output=True, text=True, timeout=10,
                creationflags=creation_flags
            )
            permissions['android.permission.READ_SMS'] = sms_result.returncode == 0
            if not permissions['android.permission.READ_SMS']:
                self.logger.warning(f"短信读取权限检查失败: {sms_result.stderr}")
            
            return permissions
        except Exception as e:
            self.logger.error(f"检查设备权限时出错: {str(e)}")
            return permissions
            