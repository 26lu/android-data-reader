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
from PyQt5.QtCore import Qt, QTimer
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

        self.refresh_interval_ms = 0  # 自动刷新间隔，0表示不自动刷新
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_contacts)

        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)

        # 搜索栏 + 刷新、导出 按钮部分
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索联系人...')
        self.search_input.textChanged.connect(self.filter_contacts)
        search_layout.addWidget(self.search_input)

        self.refresh_button = QPushButton('刷新')
        self.refresh_button.clicked.connect(self.load_contacts)
        self.refresh_button.setEnabled(True)  # 初始禁用
        search_layout.addWidget(self.refresh_button)

        self.export_button = QPushButton('导出')
        self.export_button.clicked.connect(self.export_contacts)
        search_layout.addWidget(self.export_button)

        # 添加刷新间隔输入框和启动按钮
        self.refresh_interval_input = QLineEdit()
        self.refresh_interval_input.setPlaceholderText('自动刷新间隔（秒），0为关闭')
        self.refresh_interval_input.setFixedWidth(150)
        search_layout.addWidget(self.refresh_interval_input)

        self.set_refresh_interval_button = QPushButton('设置自动刷新')
        self.set_refresh_interval_button.clicked.connect(self.set_refresh_interval)
        search_layout.addWidget(self.set_refresh_interval_button)

        layout.addLayout(search_layout)

        # 联系人表格
        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(4)
        self.contacts_table.setHorizontalHeaderLabels(['姓名', '电话', '邮箱', '分组'])
        self.contacts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.contacts_table.setSelectionBehavior(QTableWidget.SelectRows)  # 点击时选中整行
        self.contacts_table.setSelectionMode(QTableWidget.SingleSelection)  # 单选

        # 设置表头自适应填充
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 通过样式表设置选中行背景色和字体颜色
        self.contacts_table.setStyleSheet("""
        QTableWidget::item:selected {
            background-color: #a0c8f0;  /* 选中行背景色，蓝色系，可根据需求调整 */
            color: black;               /* 选中行字体颜色 */
        }
        """)

        layout.addWidget(self.contacts_table)

        self.setLayout(layout)

    def set_refresh_interval(self):
        """设置自动刷新间隔，单位秒"""
        text = self.refresh_interval_input.text().strip()
        try:
            interval_sec = int(text)
            if interval_sec < 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, '输入错误', '请输入一个非负整数秒数')
            return

        self.refresh_interval_ms = interval_sec * 1000
        if self.refresh_interval_ms > 0:
            self.refresh_timer.start(self.refresh_interval_ms)
            self.logger.info(f"设置自动刷新间隔为 {interval_sec} 秒")
        else:
            self.refresh_timer.stop()
            self.logger.info("关闭自动刷新")

    def on_device_connected(self, device_id):
        self.current_device = device_id
        self.refresh_button.setEnabled(True)
        # 设备连接时立即加载联系人
        self.load_contacts()

    def on_device_disconnected(self):
        self.current_device = None
        self.refresh_button.setEnabled(False)
        self.contacts_table.setRowCount(0)
        self.search_input.clear()
        self.refresh_timer.stop()

    def load_contacts(self):
        if not self.current_device:
            QMessageBox.warning(self, '设备未连接', '请先连接Android设备')
            return

        try:
            contacts = self.contacts_reader.get_all_contacts(self.current_device)
            self.contacts_table.clearContents()
            self.contacts_table.setRowCount(len(contacts))

            for row, contact in enumerate(contacts):
                self.contacts_table.setItem(row, 0, QTableWidgetItem(contact.name))
                phone_text = ', '.join(contact.phone) if isinstance(contact.phone, list) else str(contact.phone)
                email_text = ', '.join(contact.email) if isinstance(contact.email, list) else str(contact.email)
                self.contacts_table.setItem(row, 1, QTableWidgetItem(phone_text))
                self.contacts_table.setItem(row, 2, QTableWidgetItem(email_text))
                self.contacts_table.setItem(row, 3, QTableWidgetItem(contact.group))

            # 保持当前搜索过滤生效
            self.filter_contacts(self.search_input.text())

        except Exception as e:
            QMessageBox.critical(self, '错误', f'加载联系人失败: {str(e)}')

    def filter_contacts(self, text):
        for row in range(self.contacts_table.rowCount()):
            match = False
            for col in range(self.contacts_table.columnCount()):
                item = self.contacts_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.contacts_table.setRowHidden(row, not match)

    def export_contacts(self):
        if self.contacts_table.rowCount() == 0:
            QMessageBox.information(self, '提示', '没有联系人可以导出')
            return

        file_path, _ = QFileDialog.getSaveFileName(self, '导出联系人', '', 'CSV文件 (*.csv)')
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('姓名,电话,邮箱,分组\n')
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
