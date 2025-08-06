from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QPushButton, 
    QTableWidget, 
    QTableWidgetItem, 
    QHBoxLayout,
    QLineEdit, 
    QFileDialog, 
    QMessageBox, 
    QHeaderView
)
from PyQt5.QtCore import Qt
import logging

from ..core.device_manager import DeviceManager
from ..core.contacts_reader import ContactsReader, Contact

class ContactsTab(QWidget):
    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self.current_device = None
        self.contacts_reader = ContactsReader(device_manager)
        self.logger = logging.getLogger('ContactsTab')
        self.init_ui()
    
    def on_device_connected(self, device_id):
        """当设备连接时调用"""
        self.current_device = device_id
        self.refresh_button.setEnabled(True)
    
    def on_device_disconnected(self):
        """当设备断开连接时调用"""
        self.current_device = None
        self.refresh_button.setEnabled(False)
        self.contacts_table.setRowCount(0)
        self.search_input.clear()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 搜索栏
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索联系人...')
        self.search_input.textChanged.connect(self.filter_contacts)
        search_layout.addWidget(self.search_input)
        
        # 刷新按钮
        self.refresh_button = QPushButton('刷新')
        self.refresh_button.clicked.connect(self.load_contacts)
        self.refresh_button.setEnabled(False)  # 初始时禁用
        search_layout.addWidget(self.refresh_button)
        
        # 导出按钮
        self.export_button = QPushButton('导出')
        self.export_button.clicked.connect(self.export_contacts)
        search_layout.addWidget(self.export_button)
        
        layout.addLayout(search_layout)
        
        # 联系人表格
        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(4)
        self.contacts_table.setHorizontalHeaderLabels(['姓名', '电话', '邮箱', '分组'])
        self.contacts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.contacts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.contacts_table)
        
    def load_contacts(self):
        """加载联系人数据"""
        if not self.current_device:
            QMessageBox.warning(self, '设备未连接', '请先连接Android设备')
            return
            
        print(f"开始加载设备 {self.current_device} 的联系人数据")
        
        try:
            contacts = self.contacts_reader.get_all_contacts(self.current_device)
            print(f"从联系人读取器获取到 {len(contacts)} 个联系人")
            self.contacts_table.setRowCount(len(contacts))
            
            print(f"准备在表格中显示 {len(contacts)} 个联系人")
            
            for row, contact in enumerate(contacts):
                print(f"显示联系人 {row+1}: 姓名='{contact.name}', 电话={contact.phone}, 邮箱={contact.email}, 分组='{contact.group}'")
                
                self.contacts_table.setItem(row, 0, QTableWidgetItem(contact.name))
                # 确保电话号码和邮箱正确显示
                phone_text = ', '.join(contact.phone) if isinstance(contact.phone, list) else str(contact.phone)
                email_text = ', '.join(contact.email) if isinstance(contact.email, list) else str(contact.email)
                self.contacts_table.setItem(row, 1, QTableWidgetItem(phone_text))
                self.contacts_table.setItem(row, 2, QTableWidgetItem(email_text))
                self.contacts_table.setItem(row, 3, QTableWidgetItem(contact.group))
                
            print("联系人数据加载完成")
            
        except Exception as e:
            print(f"加载联系人时出错: {str(e)}")
            QMessageBox.critical(self, '错误', f'加载联系人失败: {str(e)}')
            
    def filter_contacts(self, text):
        """过滤联系人"""
        for row in range(self.contacts_table.rowCount()):
            match = False
            for col in range(self.contacts_table.columnCount()):
                item = self.contacts_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.contacts_table.setRowHidden(row, not match)
            
    def export_contacts(self):
        """导出联系人"""
        if self.contacts_table.rowCount() == 0:
            QMessageBox.information(self, '提示', '没有联系人可以导出')
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, '导出联系人', '', 'CSV文件 (*.csv)')
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    # 写入表头
                    f.write('姓名,电话,邮箱,分组\n')
                    
                    # 写入数据
                    for row in range(self.contacts_table.rowCount()):
                        if not self.contacts_table.isRowHidden(row):
                            name = self.contacts_table.item(row, 0).text() if self.contacts_table.item(row, 0) else ''
                            phone = self.contacts_table.item(row, 1).text() if self.contacts_table.item(row, 1) else ''
                            email = self.contacts_table.item(row, 2).text() if self.contacts_table.item(row, 2) else ''
                            group = self.contacts_table.item(row, 3).text() if self.contacts_table.item(row, 3) else ''
                            f.write(f'"{name}","{phone}","{email}","{group}"\n')
                            
                QMessageBox.information(self, '成功', f'联系人已导出到: {file_path}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'导出失败: {str(e)}')