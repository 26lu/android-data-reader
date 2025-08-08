from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QGroupBox, QProgressBar,
                             QListWidget, QListWidgetItem, QMessageBox, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from ..core.device_manager import DeviceManager

class DeviceDiagnosticTab(QWidget):
    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self.init_ui()
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.auto_check_device)
        self.check_timer.start(5000)  # 每5秒自动检查一次
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        title_label = QLabel('设备连接诊断')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                padding: 10px;
                background-color: #f0f8ff;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # 诊断控制区域
        control_layout = QHBoxLayout()
        self.check_button = QPushButton('立即诊断')
        self.check_button.clicked.connect(self.check_device_status)
        self.check_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                border: none;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            
            QPushButton:hover {
                background-color: #357ae8;
            }
            
            QPushButton:pressed {
                background-color: #2d66c3;
            }
        """)
        control_layout.addWidget(self.check_button)
        
        self.auto_check_label = QLabel('自动诊断: 每5秒')
        self.auto_check_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                padding: 10px;
            }
        """)
        control_layout.addWidget(self.auto_check_label)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # 设备状态显示区域
        status_group = QGroupBox("设备状态")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                color: #333333;
            }
        """)
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("正在检查设备状态...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                padding: 20px;
                background-color: #f8f8f8;
                border-radius: 6px;
            }
        """)
        status_layout.addWidget(self.status_label)
        
        # 连接状态指示器
        self.connection_indicator = QLabel()
        self.connection_indicator.setFixedSize(20, 20)
        self.connection_indicator.setStyleSheet("""
            QLabel {
                background-color: #cccccc;
                border-radius: 10px;
            }
        """)
        indicator_layout = QHBoxLayout()
        indicator_layout.addWidget(QLabel("连接状态:"))
        indicator_layout.addWidget(self.connection_indicator)
        indicator_layout.addStretch()
        status_layout.addLayout(indicator_layout)
        
        layout.addWidget(status_group)
        
        # 诊断结果区域
        results_group = QGroupBox("诊断结果")
        results_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                color: #333333;
            }
        """)
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 6px;
                background-color: #ffffff;
                padding: 10px;
                font-family: Consolas, monospace;
            }
        """)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                background-color: #f0f0f0;
                height: 20px;
            }
            
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 3px;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # 添加弹性空间以保持布局美观
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
    def check_device_status(self):
        """检查设备状态"""
        try:
            self.progress_bar.show()
            self.progress_bar.setRange(0, 0)  # 设置为忙碌状态
            self.status_label.setText("正在检查设备状态...")
            
            # 获取设备列表
            devices = self.device_manager.get_devices()
            
            if not devices:
                self.status_label.setText("未检测到设备")
                self.connection_indicator.setStyleSheet("background-color: #ff6b6b; border-radius: 10px;")
                self.results_text.setPlainText("❌ 未检测到任何Android设备\n\n请检查：\n1. USB线缆连接是否正常\n2. 设备是否开启USB调试\n3. 是否正确安装了设备驱动")
            else:
                device_id = devices[0]
                self.status_label.setText(f"设备已连接: {device_id}")
                self.connection_indicator.setStyleSheet("background-color: #50c878; border-radius: 10px;")
                
                # 获取设备信息
                device_info = self.device_manager.get_device_info(device_id)
                
                # 检查权限
                permissions = self.device_manager.get_device_permissions(device_id)
                
                result_text = f"✅ 检测到设备: {device_id}\n\n"
                result_text += "📱 设备信息:\n"
                for key, value in device_info.items():
                    result_text += f"  {key}: {value}\n"
                
                result_text += "\n🔒 权限状态:\n"
                for perm, granted in permissions.items():
                    status = "✅ 已授权" if granted else "❌ 未授权"
                    result_text += f"  {perm}: {status}\n"
                    
                self.results_text.setPlainText(result_text)
            
            self.progress_bar.hide()
            
        except Exception as e:
            self.status_label.setText("检查设备时出错")
            self.connection_indicator.setStyleSheet("background-color: #ff6b6b; border-radius: 10px;")
            self.results_text.setPlainText(f"❌ 检查设备时发生错误:\n{str(e)}")
            self.progress_bar.hide()
        
    def auto_check_device(self):
        """自动检查设备状态"""
        # 只在没有正在进行的手动检查时才自动检查
        if not self.progress_bar.isVisible():
            self.check_device_status()
        
    def add_result_item(self, text, status):
        """添加诊断结果项"""
        item = QListWidgetItem(text)
        if status == "success":
            item.setBackground(QColor(200, 255, 200))  # 绿色
        elif status == "warning":
            item.setBackground(QColor(255, 255, 200))  # 黄色
        elif status == "error":
            item.setBackground(QColor(255, 200, 200))  # 红色
        else:  # info
            item.setBackground(QColor(240, 240, 240))  # 灰色
            
        self.result_list.addItem(item)
        
    def update_suggestions(self, devices, permissions):
        """更新操作建议"""
        suggestions = []
        
        if not devices:
            suggestions.extend([
                "未检测到设备，请按以下步骤操作：",
                "1. 使用USB线连接Android设备到电脑",
                "2. 在设备上启用开发者选项：",
                "   - 打开设置 → 关于手机",
                "   - 连续点击'版本号'7次",
                "3. 启用USB调试：",
                "   - 返回设置 → 开发者选项",
                "   - 开启'USB调试'",
                "4. 在设备上授权电脑调试权限",
                "5. 确保设备显示为'文件传输'或'MTP'模式",
                "",
                "如果已完成以上步骤仍无法连接，请尝试：",
                "- 更换USB线缆（确保是数据线）",
                "- 更换USB端口",
                "- 安装手机品牌的官方USB驱动程序",
                "- 重新插拔USB线并确认授权提示"
            ])
        else:
            device_id = devices[0]
            storage_perm = permissions.get('存储权限', False)
            adb_perm = permissions.get('ADB调试权限', False)
            contacts_perm = permissions.get('android.permission.READ_CONTACTS', False)
            
            if not adb_perm:
                suggestions.append("ADB调试权限未授予，请在设备上确认授权对话框")
                
            if not storage_perm:
                suggestions.append("存储权限不足，请检查设备存储访问权限")
                
            if not contacts_perm:
                suggestions.append("联系人读取权限不足，部分功能可能受限")
                
            if not suggestions:
                suggestions.append("设备连接正常，可以正常使用所有功能")
            else:
                suggestions.append("")
                suggestions.append("如需完整功能，请在设备上授予相应权限")
                
        self.suggestion_text.setPlainText("\n".join(suggestions))