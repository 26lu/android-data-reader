from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt
import sys
import os
from android_reader import AndroidDataReader

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.reader = AndroidDataReader()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Android Data Reader')
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中心部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 设备状态区域
        device_layout = QHBoxLayout()
        self.device_label = QLabel('设备状态: 未连接')
        refresh_btn = QPushButton('刷新设备')
        refresh_btn.clicked.connect(self.check_device)
        device_layout.addWidget(self.device_label)
        device_layout.addWidget(refresh_btn)
        layout.addLayout(device_layout)
        
        # 设备信息区域
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        layout.addWidget(QLabel('设备信息:'))
        layout.addWidget(self.info_text)
        
        # 功能按钮区域
        btn_layout = QHBoxLayout()
        
        read_file_btn = QPushButton('读取文件')
        read_file_btn.clicked.connect(self.read_file_demo)
        btn_layout.addWidget(read_file_btn)
        
        read_image_btn = QPushButton('读取图片')
        read_image_btn.clicked.connect(self.read_image_demo)
        btn_layout.addWidget(read_image_btn)
        
        read_json_btn = QPushButton('读取JSON')
        read_json_btn.clicked.connect(self.read_json_demo)
        btn_layout.addWidget(read_json_btn)
        
        layout.addLayout(btn_layout)
        
        # 输出区域
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(QLabel('输出:'))
        layout.addWidget(self.output_text)
        
    def check_device(self):
        connected, devices = self.reader.check_device_connection()
        if connected:
            self.device_label.setText(f'设备状态: 已连接 ({", ".join(devices)})')
            # 获取并显示设备信息
            info = self.reader.get_device_info()
            info_text = '\n'.join(f'{k}: {v}' for k, v in info.items())
            self.info_text.setText(info_text)
        else:
            self.device_label.setText('设备状态: 未连接')
            self.info_text.clear()
    
    def read_file_demo(self):
        # 读取一个示例文本文件
        content = self.reader.read_file('/sdcard/test.txt')
        if content:
            self.output_text.setText(f'文件内容:\n{content}')
        else:
            QMessageBox.warning(self, '错误', '无法读取文件')
    
    def read_image_demo(self):
        # 读取一个示例图片文件
        image_path = self.reader.read_image('/sdcard/test.jpg')
        if image_path:
            self.output_text.setText(f'图片已保存到: {image_path}')
        else:
            QMessageBox.warning(self, '错误', '无法读取图片')
    
    def read_json_demo(self):
        # 读取一个示例JSON文件
        data = self.reader.read_json_data('/sdcard/test.json')
        if data:
            self.output_text.setText(f'JSON数据:\n{data}')
        else:
            QMessageBox.warning(self, '错误', '无法读取JSON数据')
