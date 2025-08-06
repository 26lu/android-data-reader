# src/ui/photos_tab.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                             QListWidget, QListWidgetItem, QHBoxLayout,
                             QLineEdit, QFileDialog, QMessageBox, QLabel,
                             QProgressBar, QSizePolicy, QSplitter)
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
        main_layout = QVBoxLayout(self)

        # 搜索和按钮区域
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索照片...')
        self.search_input.textChanged.connect(self.filter_photos)
        search_layout.addWidget(self.search_input)

        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton('刷新')
        self.refresh_button.clicked.connect(self.load_photos)
        self.refresh_button.setEnabled(True)
        button_layout.addWidget(self.refresh_button)

        self.export_button = QPushButton('导出选中')
        self.export_button.clicked.connect(self.export_selected_photos)
        button_layout.addWidget(self.export_button)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()

        # 照片列表
        self.photo_list = QListWidget()
        self.photo_list.setViewMode(QListWidget.IconMode)
        self.photo_list.setIconSize(QSize(128, 128))
        self.photo_list.setSpacing(10)
        self.photo_list.setResizeMode(QListWidget.Adjust)
        self.photo_list.setSelectionMode(QListWidget.MultiSelection)
        self.photo_list.itemClicked.connect(self.on_photo_selected)  # 绑定点击事件

        # 显示大图的 QLabel
        self.photo_preview = QLabel()
        self.photo_preview.setAlignment(Qt.AlignCenter)
        self.photo_preview.setMinimumSize(400, 400)
        self.photo_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.photo_preview.setText("请选择左侧照片查看预览")

        # 状态标签
        self.status_label = QLabel()

        # 用 QSplitter 实现左右分栏：左边照片列表，右边大图预览
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addLayout(search_layout)
        left_layout.addLayout(button_layout)
        left_layout.addWidget(self.progress_bar)
        left_layout.addWidget(self.photo_list)
        left_layout.addWidget(self.status_label)

        splitter.addWidget(left_widget)
        splitter.addWidget(self.photo_preview)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)

        main_layout.addWidget(splitter)

        try:
            os.makedirs(self.thumb_dir, exist_ok=True)
        except Exception as e:
            self.logger.warning(f"无法创建缩略图目录 {self.thumb_dir}: {e}")

    def on_photo_selected(self, item: QListWidgetItem):
        photo: PhotoInfo = item.data(Qt.UserRole)
        thumb_path = os.path.join(self.thumb_dir, f"thumb_{os.path.basename(photo.path)}")

        if os.path.exists(thumb_path):
            pixmap = QPixmap(thumb_path)
        else:
            try:
                local_path = self.photos_reader.download_photo(photo, self.thumb_dir, self.current_device)
                if local_path and os.path.exists(local_path):
                    pixmap = QPixmap(local_path)
                else:
                    pixmap = QPixmap()
            except Exception as e:
                self.logger.error(f"下载图片失败: {e}")
                pixmap = QPixmap()

        if pixmap.isNull():
            self.photo_preview.clear()
            self.photo_preview.setText("无法显示该图片")
        else:
            # 大图自适应右侧 QLabel 大小
            scaled_pixmap = pixmap.scaled(
                self.photo_preview.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.photo_preview.setPixmap(scaled_pixmap)



    def resizeEvent(self, event):
        # 当窗口大小变化时，如果有图片，重新缩放显示
        if self.photo_preview.pixmap():
            scaled_pixmap = self.photo_preview.pixmap().scaled(
                self.photo_preview.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.photo_preview.setPixmap(scaled_pixmap)
        super().resizeEvent(event)

    def filter_photos(self, text: str):
        text = text.lower()
        for i in range(self.photo_list.count()):
            item = self.photo_list.item(i)
            photo = item.data(Qt.UserRole)
            filename = os.path.basename(photo.path).lower()
            date_str = datetime.fromtimestamp(photo.date / 1000).strftime('%Y-%m-%d %H:%M:%S').lower()
            # 判断搜索关键字是否出现在文件名或时间字符串里
            match = (text in filename) or (text in date_str)
            item.setHidden(not match)

    def load_photos(self):
        if not self.current_device:
            QMessageBox.warning(self, "警告", "未连接设备，无法加载照片")
            return

        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.photo_list.clear()
        self.photo_data = []

        try:
            self.photo_data = self.photos_reader.scan_photos(self.current_device)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载照片失败: {e}")
            self.progress_bar.hide()
            return

        self.progress_bar.setMaximum(len(self.photo_data))

        for i, photo in enumerate(self.photo_data):
            item = QListWidgetItem()
            filename = os.path.basename(photo.path)
            date_str = datetime.fromtimestamp(photo.date / 1000).strftime('%Y-%m-%d %H:%M:%S')
            # 设置文字：文件名和日期
            item.setText(f"{filename}\n{date_str}")
            item.setData(Qt.UserRole, photo)

            thumb_path = os.path.join(self.thumb_dir, f"thumb_{filename}")
            if os.path.exists(thumb_path):
                pixmap = QPixmap(thumb_path)
                if not pixmap.isNull():
                    # 缩略图设置为小图标，大小128x128
                    item.setIcon(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            self.photo_list.addItem(item)
            self.progress_bar.setValue(i + 1)

        self.progress_bar.hide()
        self.status_label.setText(f"共加载 {len(self.photo_data)} 张照片")


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

    def on_device_connected(self, device_id: str):
        """设备连接时调用"""
        self.current_device = device_id
        self.refresh_button.setEnabled(True)
        self.status_label.setText(f"设备已连接: {device_id}")

    def on_device_disconnected(self):
        """设备断开时调用"""
        self.current_device = None
        self.refresh_button.setEnabled(False)
        self.photo_list.clear()
        self.photo_data.clear()
        self.status_label.setText("设备已断开，无法加载照片")
        self.photo_preview.clear()
        self.photo_preview.setText("请选择左侧照片查看预览")
