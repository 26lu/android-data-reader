# src/ui/photos_tab.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                             QListWidget, QListWidgetItem, QHBoxLayout,
                             QLineEdit, QFileDialog, QMessageBox, QLabel,
                             QProgressBar)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap
import os
import logging
from datetime import datetime
from typing import List

from src.core.device_manager import DeviceManager
from src.core.logger import default_logger
from src.core.photos_reader import PhotosReader, PhotoInfo  # 重点：导入

class PhotosTab(QWidget):
    def __init__(self, device_manager: DeviceManager):
        super().__init__()
        self.device_manager = device_manager
        self.current_device = None
        self.photo_data: List[PhotoInfo] = []
        self.thumb_dir = 'thumbnails'
        self.photos_reader = PhotosReader(device_manager)
        self.logger = logging.getLogger('PhotosTab')
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索照片...')
        self.search_input.textChanged.connect(self.filter_photos)
        search_layout.addWidget(self.search_input)

        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton('刷新')
        self.refresh_button.clicked.connect(self.load_photos)
        self.refresh_button.setEnabled(False)
        button_layout.addWidget(self.refresh_button)

        self.export_button = QPushButton('导出选中')
        self.export_button.clicked.connect(self.export_selected_photos)
        button_layout.addWidget(self.export_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.hide()

        self.photo_list = QListWidget()
        self.photo_list.setViewMode(QListWidget.IconMode)
        self.photo_list.setIconSize(QSize(128, 128))
        self.photo_list.setSpacing(10)
        self.photo_list.setResizeMode(QListWidget.Adjust)
        self.photo_list.setSelectionMode(QListWidget.MultiSelection)

        self.status_label = QLabel()

        layout.addLayout(search_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.photo_list)
        layout.addWidget(self.status_label)

        try:
            os.makedirs(self.thumb_dir, exist_ok=True)
        except Exception as e:
            self.logger.warning(f"无法创建缩略图目录 {self.thumb_dir}: {e}")

    def on_device_connected(self, device_id: str):
        self.current_device = device_id
        self.refresh_button.setEnabled(True)

    def on_device_disconnected(self):
        self.current_device = None
        self.refresh_button.setEnabled(False)
        self.photo_list.clear()
        self.photo_data.clear()

    def load_photos(self):
        if not self.current_device:
            return
        try:
            self.photo_data = self.photos_reader.scan_photos(self.current_device)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'加载照片失败: {str(e)}')
            self.progress_bar.hide()
            return

        self.progress_bar.setMaximum(len(self.photo_data))
        self.progress_bar.setValue(0)
        self.progress_bar.show()

        self.photo_list.clear()
        for i, photo in enumerate(self.photo_data):
            item = QListWidgetItem()
            filename = os.path.basename(photo.path)
            date_str = datetime.fromtimestamp(photo.date / 1000).strftime('%Y-%m-%d %H:%M:%S')
            item.setText(f"{filename}\n{date_str}")
            item.setData(Qt.UserRole, photo)

            thumb_path = os.path.join(self.thumb_dir, f"thumb_{filename}")
            if os.path.exists(thumb_path):
                pixmap = QPixmap(thumb_path)
                if not pixmap.isNull():
                    item.setIcon(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            self.photo_list.addItem(item)
            self.progress_bar.setValue(i + 1)

        self.progress_bar.hide()
        self.status_label.setText(f"共加载 {len(self.photo_data)} 张照片")

    def filter_photos(self, text: str):
        text = text.lower()
        for i in range(self.photo_list.count()):
            item = self.photo_list.item(i)
            photo = item.data(Qt.UserRole)
            filename = os.path.basename(photo.path).lower()
            date_str = datetime.fromtimestamp(photo.date / 1000).strftime('%Y-%m-%d %H:%M:%S').lower()
            match = (text in filename) or (text in date_str)
            item.setHidden(not match)

    def export_selected_photos(self):
        selected_items = self.photo_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, '提示', '请先选择要导出的照片')
            return

        directory = QFileDialog.getExistingDirectory(self, '选择导出目录')
        if not directory:
            return

        success_count = 0
        for item in selected_items:
            photo = item.data(Qt.UserRole)
            try:
                local_path = self.photos_reader.download_photo(photo, directory, self.current_device)
                if local_path:
                    success_count += 1
            except Exception as e:
                self.logger.error(f"导出照片失败: {e}")

        QMessageBox.information(self, '导出完成', f'成功导出 {success_count} 张照片')
