from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QGroupBox, QProgressBar,
                             QListWidget, QListWidgetItem, QMessageBox)
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
        
        # 标题
        title_label = QLabel('设备连接诊断')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 诊断控制区域
        control_layout = QHBoxLayout()
        self.check_button = QPushButton('立即诊断')
        self.check_button.clicked.connect(self.check_device_status)
        control_layout.addWidget(self.check_button)
        
        self.auto_check_label = QLabel('自动诊断: 每5秒')
        control_layout.addWidget(self.auto_check_label)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # 诊断进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 诊断结果区域
        self.result_group = QGroupBox('诊断结果')
        result_layout = QVBoxLayout(self.result_group)
        
        self.result_list = QListWidget()
        result_layout.addWidget(self.result_list)
        
        layout.addWidget(self.result_group)
        
        # 操作建议区域
        self.suggestion_group = QGroupBox('操作建议')
        suggestion_layout = QVBoxLayout(self.suggestion_group)
        
        self.suggestion_text = QTextEdit()
        self.suggestion_text.setReadOnly(True)
        suggestion_layout.addWidget(self.suggestion_text)
        
        layout.addWidget(self.suggestion_group)
        
        # 初始诊断
        self.check_device_status()
        
    def check_device_status(self):
        """检查设备状态"""
        self.progress_bar.setVisible(True)
        self.result_list.clear()
        
        try:
            # 检查ADB设备
            devices = self.device_manager.get_devices()
            self.add_result_item(f"ADB设备检测: 找到 {len(devices)} 个设备", 
                               "success" if devices else "warning")
            
            if devices:
                device_id = devices[0]
                self.add_result_item(f"设备ID: {device_id}", "info")
                
                # 检查设备信息
                device_info = self.device_manager.get_device_info(device_id)
                if device_info:
                    model = device_info.get('model', '未知')
                    android_version = device_info.get('android_version', '未知')
                    manufacturer = device_info.get('manufacturer', '未知')
                    self.add_result_item(f"设备型号: {model}", "info")
                    self.add_result_item(f"Android版本: {android_version}", "info")
                    self.add_result_item(f"制造商: {manufacturer}", "info")
                
                # 检查权限
                permissions = self.device_manager.check_permissions(device_id)
                storage_perm = permissions.get('存储权限', False)
                adb_perm = permissions.get('ADB调试权限', False)
                contacts_perm = permissions.get('android.permission.READ_CONTACTS', False)
                
                self.add_result_item(f"存储权限: {'已授予' if storage_perm else '未授予'}", 
                                   "success" if storage_perm else "error")
                self.add_result_item(f"ADB调试权限: {'已授予' if adb_perm else '未授予'}", 
                                   "success" if adb_perm else "error")
                self.add_result_item(f"联系人读取权限: {'已授予' if contacts_perm else '未授予'}", 
                                   "success" if contacts_perm else "error")
                
                # 提供针对性建议
                self.update_suggestions(devices, permissions)
            else:
                # 没有检测到设备，提供连接指导
                self.update_suggestions(devices, {})
                
        except Exception as e:
            self.add_result_item(f"诊断过程中出错: {str(e)}", "error")
            self.update_suggestions([], {})
            
        self.progress_bar.setVisible(False)
        
    def auto_check_device(self):
        """自动检查设备状态"""
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