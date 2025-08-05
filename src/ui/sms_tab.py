from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHBoxLayout,
                             QLineEdit, QFileDialog, QMessageBox, QSplitter,
                             QTextEdit)
from PyQt5.QtCore import Qt
from ..core.device_manager import DeviceManager
from ..core.sms_reader import SMSReader

class SMSTab(QWidget):
    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self.current_device = None
        self.sms_reader = SMSReader(device_manager)
        self.messages = []  # 添加messages属性初始化
        self.init_ui()
    
    def on_device_connected(self, device_id):
        """当设备连接时调用"""
        self.current_device = device_id
        self.refresh_button.setEnabled(True)
    
    def on_device_disconnected(self):
        """当设备断开连接时调用"""
        self.current_device = None
        self.refresh_button.setEnabled(False)
        self.sms_list.clear()
        self.search_input.clear()
        self.messages = []  # 清空消息列表
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 搜索栏
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索短信...')
        self.search_input.textChanged.connect(self.filter_messages)
        search_layout.addWidget(self.search_input)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton('刷新')
        self.refresh_button.clicked.connect(self.load_messages)
        self.export_button = QPushButton('导出')
        self.export_button.clicked.connect(self.export_messages)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.export_button)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 会话列表
        self.sms_list = QTableWidget()
        self.sms_list.setColumnCount(2)
        self.sms_list.setHorizontalHeaderLabels(['联系人', '最后消息时间'])
        self.sms_list.horizontalHeader().setStretchLastSection(True)
        self.sms_list.currentItemChanged.connect(self.show_conversation)
        
        # 消息详情
        self.message_view = QTextEdit()
        self.message_view.setReadOnly(True)
        
        # 添加到分割器
        splitter.addWidget(self.sms_list)
        splitter.addWidget(self.message_view)
        
        # 添加到主布局
        layout.addLayout(search_layout)
        layout.addLayout(button_layout)
        layout.addWidget(splitter)
        
        # 加载短信
        self.load_messages()
        
    def load_messages(self):
        """加载短信数据"""
        if not self.current_device:
            QMessageBox.warning(self, '警告', '请先连接设备')
            return
            
        self.messages = self.sms_reader.get_all_sms(self.current_device)
        self.conversations = self.sms_reader.get_conversations(self.current_device)
        self.update_conversation_table()
        
    def update_conversation_table(self):
        """更新会话列表"""
        self.sms_list.setRowCount(len(self.conversations))
        
        for row, (phone, messages) in enumerate(self.conversations.items()):
            if messages:
                latest = messages[-1]
                self.sms_list.setItem(row, 0, QTableWidgetItem(phone))
                self.sms_list.setItem(row, 1, QTableWidgetItem(latest.time))
                
    def show_conversation(self, current, previous):
        """显示选中的会话内容"""
        if not current:
            return
            
        phone = self.sms_list.item(current.row(), 0).text()
        messages = self.conversations.get(phone, [])
        
        # 格式化会话内容
        html = []
        for msg in messages:
            align = 'right' if msg.type == 'sent' else 'left'
            color = '#DCF8C6' if msg.type == 'sent' else '#FFFFFF'
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
        """根据搜索框内容过滤消息"""
        search_text = self.search_input.text().lower()
        
        if not search_text:
            self.update_conversation_table()
            return
            
        filtered_conversations = {}
        for phone, messages in self.conversations.items():
            matching_messages = [
                msg for msg in messages
                if search_text in msg.content.lower() or
                   search_text in phone.lower()
            ]
            if matching_messages:
                filtered_conversations[phone] = matching_messages
                
        self.conversations = filtered_conversations
        self.update_conversation_table()
        
    def export_messages(self):
        """导出短信数据"""
        if not self.messages:
            QMessageBox.warning(self, '警告', '没有可导出的短信数据')
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            '导出短信',
            'messages.json',
            'JSON文件 (*.json)'
        )
        
        if file_path:
            try:
                self.sms_reader.save_messages(self.messages, file_path)
                QMessageBox.information(
                    self,
                    '成功',
                    f'短信数据已导出到: {file_path}'
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    '错误',
                    f'导出失败: {str(e)}'
                )
