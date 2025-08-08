import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHBoxLayout,
                             QLineEdit, QFileDialog, QMessageBox, QSplitter,
                             QTextEdit)
from PyQt5.QtCore import Qt
from ..core.device_manager import DeviceManager
from ..core.sms_reader import SMSReader


class SMSTab(QWidget):
    def __init__(self, device_manager: DeviceManager):
        super().__init__()
        self.device_manager = device_manager
        self.current_device = None
        self.sms_reader = SMSReader(device_manager)
        self.messages = []  # 所有短信
        self.conversations = {}  # 分组会话短信
        self.init_ui()

    def on_device_connected(self, device_id):
        """设备连接回调"""
        self.current_device = device_id
        self.refresh_button.setEnabled(True)

    def on_device_disconnected(self):
        """设备断开回调"""
        self.current_device = None
        self.refresh_button.setEnabled(False)
        self.sms_list.clear()
        self.search_input.clear()
        self.messages = []
        self.conversations = {}

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 搜索框
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索短信...')
        self.search_input.textChanged.connect(self.filter_messages)
        search_layout.addWidget(self.search_input)

        # 按钮区
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton('刷新')
        self.refresh_button.clicked.connect(self.load_messages)
        
        # 添加刷新间隔设置（类似联系人标签页）
        self.refresh_interval_input = QLineEdit()
        self.refresh_interval_input.setPlaceholderText('自动刷新间隔（秒），0为关闭')
        self.refresh_interval_input.setFixedWidth(150)
        self.refresh_interval_input.setText("30")  # 默认30秒
        
        self.set_refresh_interval_button = QPushButton('设置自动刷新')
        self.set_refresh_interval_button.clicked.connect(self.set_refresh_interval)
        
        self.export_button = QPushButton('导出选中会话')
        self.export_button.clicked.connect(self.export_selected_conversation)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.refresh_interval_input)
        button_layout.addWidget(self.set_refresh_interval_button)
        button_layout.addWidget(self.export_button)

        # 分割器 - 左侧会话，右侧详情
        splitter = QSplitter(Qt.Horizontal)

        self.sms_list = QTableWidget()
        self.sms_list.setColumnCount(2)
        self.sms_list.setHorizontalHeaderLabels(['联系人', '最后消息时间'])
        self.sms_list.horizontalHeader().setStretchLastSection(True)
        self.sms_list.currentItemChanged.connect(self.show_conversation)

        self.message_view = QTextEdit()
        self.message_view.setReadOnly(True)

        splitter.addWidget(self.sms_list)
        splitter.addWidget(self.message_view)

        layout.addLayout(search_layout)
        layout.addLayout(button_layout)
        layout.addWidget(splitter)

        self.refresh_button.setEnabled(False)
        self.load_messages()

    def load_messages(self):
        if not self.current_device:
            QMessageBox.warning(self, '警告', '请先连接设备')
            return

        self.messages = self.sms_reader.get_all_sms(self.current_device)
        self.conversations = self.sms_reader.get_conversations(self.current_device)
        self.update_conversation_table()

    def update_conversation_table(self):
        self.sms_list.setRowCount(len(self.conversations))
        for row, (phone, messages) in enumerate(self.conversations.items()):
            if messages:
                latest = messages[-1]
                self.sms_list.setItem(row, 0, QTableWidgetItem(phone))
                self.sms_list.setItem(row, 1, QTableWidgetItem(latest.time))

    def show_conversation(self, current, previous):
        if not current:
            self.message_view.clear()
            return

        phone = self.sms_list.item(current.row(), 0).text()
        messages = self.conversations.get(phone, [])

        html = []
        for msg in messages:
            align = 'right' if msg.type == 2 else 'left'  # 2一般代表发出短信
            color = '#DCF8C6' if msg.type == 2 else '#FFFFFF'
            html.append(f'''
                <div style="text-align: {align}; margin: 10px;">
                    <div style="display: inline-block; background: {color};
                              padding: 10px; border-radius: 10px; max-width: 80%;">
                        <div style="color: #666666; font-size: 12px;">
                            {msg.time}
                        </div>
                        <div style="margin-top: 5px;">
                            {msg.content}
                        </div>
                    </div>
                </div>
            ''')

        self.message_view.setHtml(''.join(html))

    def filter_messages(self):
        search_text = self.search_input.text().lower()
        if not search_text:
            # 还原完整会话列表
            self.load_messages()
            return

        filtered = {}
        for phone, messages in self.conversations.items():
            matched = [m for m in messages if search_text in m.content.lower() or search_text in phone.lower()]
            if matched:
                filtered[phone] = matched
        self.conversations = filtered
        self.update_conversation_table()

    def export_selected_conversation(self):
        current_item = self.sms_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, '警告', '请先选择一个会话')
            return

        phone = self.sms_list.item(current_item.row(), 0).text()
        messages_to_export = self.conversations.get(phone, [])

        if not messages_to_export:
            QMessageBox.warning(self, '警告', '选中会话没有短信数据')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            '导出短信',
            f'{phone}_messages.json',
            'JSON文件 (*.json)'
        )

        if file_path:
            try:
                self.sms_reader.save_sms(messages_to_export, file_path)
                QMessageBox.information(self, '成功', f'短信数据已导出到: {file_path}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'导出失败: {str(e)}')

    def update_refresh_interval(self, value):
        """更新刷新间隔"""
        self.refresh_interval = value * 1000  # 转换为毫秒
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
            self.refresh_timer.start(self.refresh_interval)

    def set_refresh_interval(self):
        """设置自动刷新间隔"""
        interval_sec = self.refresh_interval_spinbox.value()
        self.refresh_interval = interval_sec * 1000
        if self.refresh_interval > 0:
            if self.current_device:  # 只有在设备连接时才启动定时器
                self.refresh_timer.start(self.refresh_interval)
            self.logger.info(f"设置自动刷新间隔为 {interval_sec} 秒")
        else:
            self.refresh_timer.stop()
            self.logger.info("关闭自动刷新")
