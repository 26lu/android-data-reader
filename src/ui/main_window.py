from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QPushButton, QLabel,
                             QMessageBox, QStatusBar, QHBoxLayout)
import logging
from PyQt5.QtCore import Qt
from ..core.device_manager import DeviceManager
from .contacts_tab import ContactsTab
from .sms_tab import SMSTab
from .photos_tab import PhotosTab
from .device_diagnostic_tab import DeviceDiagnosticTab
import logging
import os
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.device_manager = DeviceManager()
        self.current_device = None
        self.initUI()

    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle('Android数据读取器')
        self.setGeometry(100, 100, 1000, 700)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 设备状态部分
        status_layout = QHBoxLayout()
        self.device_status = QLabel('未连接设备')
        self.refresh_button = QPushButton('刷新设备')
        self.refresh_button.clicked.connect(self.refresh_device_status)

        status_layout.addWidget(self.device_status)
        status_layout.addWidget(self.refresh_button)
        layout.addLayout(status_layout)

        # 创建标签页
        self.tab_widget = QTabWidget()
        self.contacts_tab = ContactsTab(self.device_manager)
        self.sms_tab = SMSTab(self.device_manager)
        self.photos_tab = PhotosTab(self.device_manager)
        self.device_diagnostic_tab = DeviceDiagnosticTab(self.device_manager)

        self.tab_widget.addTab(self.contacts_tab, '通讯录')
        self.tab_widget.addTab(self.sms_tab, '短信')
        self.tab_widget.addTab(self.photos_tab, '相册')
        self.tab_widget.addTab(self.device_diagnostic_tab, '设备诊断')

        layout.addWidget(self.tab_widget)

        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # 初次检查设备状态
        self.refresh_device_status()

    def refresh_device_status(self):
        """刷新设备状态显示"""
        try:
            devices = self.device_manager.get_devices()
            if devices:
                self.current_device = devices[0]
                device_info = self.device_manager.get_device_info(self.current_device)
                self.device_status.setText(f'已连接: {device_info.get("model", "未知设备")}')
                self.statusBar.showMessage(f'设备已连接: {self.current_device}')
                # 启用所有标签页
                self.contacts_tab.setEnabled(True)
                self.sms_tab.setEnabled(True)
                self.photos_tab.setEnabled(True)
                # 通知标签页设备已连接
                self.contacts_tab.on_device_connected(self.current_device)
                self.sms_tab.on_device_connected(self.current_device)
                self.photos_tab.on_device_connected(self.current_device)
            else:
                self.current_device = None
                self.device_status.setText('未连接设备')
                self.statusBar.showMessage('请连接设备并启用USB调试')

                # 提供更详细的指导信息
                guidance_text = (
                    "未检测到Android设备，请按以下步骤操作：\n\n"
                    "1. 使用USB线连接Android设备到电脑\n"
                    "2. 在设备上启用开发者选项：\n"
                    "   - 打开设置 -> 关于手机\n"
                    "   - 连续点击'版本号'7次\n"
                    "3. 启用USB调试：\n"
                    "   - 返回设置 -> 开发者选项\n"
                    "   - 开启'USB调试'\n"
                    "4. 在设备上授权电脑调试权限\n"
                    "5. 确保设备显示为'文件传输'或'MTP'模式\n\n"
                    "如果已完成以上步骤仍无法连接，请尝试：\n"
                    "- 更换USB线缆（确保是数据线）\n"
                    "- 更换USB端口\n"
                    "- 安装手机品牌的官方USB驱动程序\n"
                    "- 重新插拔USB线并确认授权提示\n\n"
                    "注意：这些步骤是Android系统安全机制的一部分，"
                    "用于保护您的隐私和数据安全。"
                )
                # self.device_guidance.setText(guidance_text)
                # 通知标签页设备已断开连接
                self.contacts_tab.on_device_disconnected()
                self.sms_tab.on_device_disconnected()
                self.photos_tab.on_device_disconnected()
        except Exception as e:
            logging.error(f"刷新设备状态时出错: {str(e)}")
            self.current_device = None
            self.device_status.setText('设备状态错误')
            self.statusBar.showMessage('设备状态检测出错')

    def closeEvent(self, event):
        """关闭窗口时的处理"""
        reply = QMessageBox.question(
            self, '确认', '确定要退出吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 清理临时文件
            self.cleanup_temp_files()
            # 确保完全退出应用
            import sys
            sys.exit(0)
        else:
            event.ignore()

    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            # 清理照片标签页的缩略图目录
            if hasattr(self, 'photos_tab') and self.photos_tab:
                import shutil
                # 清理照片标签页的缩略图目录
                if os.path.exists(self.photos_tab.thumb_dir):
                    shutil.rmtree(self.photos_tab.thumb_dir)
                    self.photos_tab.logger.info(f"已删除缩略图目录: {self.photos_tab.thumb_dir}")

                # 清理照片读取器的缩略图目录
                if hasattr(self.photos_tab, 'photos_reader') and self.photos_tab.photos_reader:
                    photo_reader = self.photos_tab.photos_reader
                    if hasattr(photo_reader, 'thumbnail_dir') and os.path.exists(photo_reader.thumbnail_dir):
                        shutil.rmtree(photo_reader.thumbnail_dir)
                        photo_reader.logger.info(f"已删除照片读取器缩略图目录: {photo_reader.thumbnail_dir}")

            # 清理可能存在的其他临时目录
            temp_dirs = ['thumbnails', 'temp', '.cache']
            for temp_dir in temp_dirs:
                abs_temp_dir = os.path.abspath(temp_dir)
                if os.path.exists(abs_temp_dir) and abs_temp_dir not in ['.', '..']:
                    import shutil
                    shutil.rmtree(abs_temp_dir)
                    logging.info(f"已删除临时目录: {abs_temp_dir}")

        except Exception as e:
            logging.error(f"清理临时文件时出错: {str(e)}")
