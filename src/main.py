#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Android数据读取器主程序入口
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication, QMessageBox

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logging.info("Android数据读取器启动")

def check_expiration():
    """检查程序是否过期"""
    # 程序构建日期（这个会在打包时由脚本替换）
    BUILD_DATE = "2025-08-06"

    try:
        build_date = datetime.strptime(BUILD_DATE, "%Y-%m-%d")
        expiration_date = build_date + timedelta(days=200)
        current_date = datetime.now()

        if current_date > expiration_date:
            # 程序已过期
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "程序已过期",
                f"此程序已于{expiration_date.strftime('%Y-%m-%d')}过期，无法继续使用。\n请获取新版本。"
            )
            return False
        else:
            # 显示剩余天数
            remaining_days = (expiration_date - current_date).days
            logging.info(f"程序将在 {expiration_date.strftime('%Y-%m-%d')} 过期，剩余 {remaining_days} 天")
            return True
    except Exception as e:
        logging.error(f"检查过期时间时出错: {e}")
        return True  # 出错时允许继续运行

def main():
    """主函数"""
    setup_logging()
    logging.info("Android数据读取器启动")

    # 检查程序是否过期
    if not check_expiration():
        sys.exit(1)

    # 导入UI模块（延迟导入以避免在过期检查前加载不必要的模块）
    from src.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Android数据读取器")
    app.setApplicationVersion("1.0.0")

    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"应用程序启动失败: {e}")
        QMessageBox.critical(None, "错误", f"应用程序启动失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
