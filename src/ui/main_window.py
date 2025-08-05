from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QPushButton, QLabel,
                             QMessageBox, QStatusBar, QHBoxLayout)
from PyQt5.QtCore import Qt
from ..core.device_manager import DeviceManager
from .contacts_tab import ContactsTab
from .sms_tab import SMSTab
from .photos_tab import PhotosTab
import logging

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
        
        self.tab_widget.addTab(self.contacts_tab, '通讯录')
        self.tab_widget.addTab(self.sms_tab, '短信')
        self.tab_widget.addTab(self.photos_tab, '照片')
        
        layout.addWidget(self.tab_widget)
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # 初次检查设备状态
        self.refresh_device_status()
        
    def refresh_device_status(self):
        """刷新设备连接状态"""
        try:
            devices = self.device_manager.get_devices()
            if devices:
                # 使用第一个设备作为当前设备
                self.current_device = devices[0]
                device_info = self.device_manager.get_device_info(self.current_device)
                status_text = f"已连接设备: {device_info.get('型号', '未知型号')} ({self.current_device})"
                self.device_status.setText(status_text)
                self.statusBar.showMessage('设备已连接')
                
                # 检查权限
                permissions = self.device_manager.get_device_permissions(self.current_device)
                if not all(permissions.values()):
                    QMessageBox.warning(
                        self,
                        '权限提醒',
                        '部分权限未授予，可能影响功能使用。\n请在设备上授予所需权限。'
                    )
                
                # 通知各个标签页设备已连接
                self.contacts_tab.on_device_connected(self.current_device)
                self.sms_tab.on_device_connected(self.current_device)
                self.photos_tab.on_device_connected(self.current_device)
            else:
                self.current_device = None
                self.device_status.setText('未连接设备')
                self.statusBar.showMessage('请连接设备')
                
                # 通知各个标签页设备已断开
                self.contacts_tab.on_device_disconnected()
                self.sms_tab.on_device_disconnected()
                self.photos_tab.on_device_disconnected()
        except Exception as e:
            logging.error(f"刷新设备状态时出错: {e}")
            self.current_device = None
            self.device_status.setText('设备状态检查失败')
            self.statusBar.showMessage('设备状态检查失败')
            
    def closeEvent(self, event):
        """关闭窗口时的处理"""
        reply = QMessageBox.question(
            self, '确认', '确定要退出吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()