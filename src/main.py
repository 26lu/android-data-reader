#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Android数据读取器主程序入口
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from .ui.main_window import MainWindow

def setup_logging():
    """设置日志配置"""
    # 创建logs目录（如果不存在）
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception as e:
            print(f"警告: 无法创建日志目录 {log_dir}: {e}")
    
    # 配置日志
    log_file = os.path.join(log_dir, 'android_reader.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logging.info("Android数据读取器启动")

def main():
    """主函数"""
    setup_logging()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()