#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志配置模块
"""

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name=__name__, log_file=None, level=logging.INFO):
    """
    设置日志记录器
    
    Args:
        name (str): 日志记录器名称
        log_file (str): 日志文件路径，默认为None
        level: 日志级别
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，则添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except Exception as e:
                # 如果无法创建日志目录，打印警告但继续执行
                print(f"警告: 无法创建日志目录 {log_dir}: {e}")
        
        # 使用循环文件处理器，避免日志文件过大
        try:
            file_handler = RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # 如果无法创建文件处理器，打印警告但继续执行
            print(f"警告: 无法创建文件日志处理器 {log_file}: {e}")
    
    return logger

# 创建默认日志记录器
default_logger = setup_logger(
    'android_reader', 
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'android_reader.log')
)