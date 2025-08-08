from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QHBoxLayout, QLineEdit, QFileDialog, QMessageBox, QLabel,
    QProgressBar, QSizePolicy, QSplitter
)
from PyQt5.QtCore import Qt, QSize, QRunnable, QThreadPool, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QIcon, QFontMetrics
import os
import logging
from datetime import datetime
from typing import List

from src.core.device_manager import DeviceManager
from src.core.photos_reader import PhotosReader, PhotoInfo


class ThumbLoaderSignals(QObject):
    finished = pyqtSignal(object, object)  # 改为object类型，兼容所有对象


class ThumbLoader(QRunnable):
    """线程池异步加载缩略图"""
    def __init__(self, photo: PhotoInfo, item: QListWidgetItem,
                 photos_reader: PhotosReader, device_id: str, thumb_dir: str):
        super().__init__()
        self.photo = photo
        self.item = item
        self.photos_reader = photos_reader
        self.device_id = device_id
        self.thumb_dir = thumb_dir
        self.signals = ThumbLoaderSignals()

    def run(self):
        filename = os.path.basename(self.photo.path)
        thumb_path = os.path.join(self.thumb_dir, f"thumb_{filename}")
        pixmap = None

        if os.path.exists(thumb_path):
            pixmap = QPixmap(thumb_path)
        else:
            try:
                local_path = self.photos_reader.download_photo(self.photo, self.thumb_dir, self.device_id)
                if local_path and os.path.exists(local_path):
                    pixmap = QPixmap(local_path)
            except Exception as e:
                logging.getLogger('PhotosTab').warning(f"缩略图下载失败: {e}")

        if pixmap and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon = QIcon(scaled_pixmap)
            self.signals.finished.emit(self.item, icon)


class PhotosTab(QWidget):
    PAGE_SIZE = 50  # 每次加载照片数量

    class PhotoItemWidget(QWidget):
        def __init__(self, photo: PhotoInfo, pixmap=None):
            super().__init__()
            self.photo = photo
            layout = QHBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(10)

            # 缩略图标签，固定大小128x128，左边垂直居中
            self.thumb_label = QLabel()
            self.thumb_label.setFixedSize(128, 128)
            self.thumb_label.setAlignment(Qt.AlignCenter)
            if pixmap:
                scaled = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.thumb_label.setPixmap(scaled)
            layout.addWidget(self.thumb_label, 0, Qt.AlignVCenter)

            # 右边竖直布局放文件名和日期
            text_layout = QVBoxLayout()
            text_layout.setContentsMargins(0, 0, 0, 0)
            text_layout.setSpacing(5)

            filename = os.path.basename(photo.path)
            font = self.font()
            metrics = QFontMetrics(font)
            elided_filename = metrics.elidedText(filename, Qt.ElideRight, 180)
            self.name_label = QLabel(elided_filename)
            self.name_label.setStyleSheet("font-weight: bold;")
            self.name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.name_label.setToolTip(filename)  # 鼠标悬停显示完整文件名

            date_str = datetime.fromtimestamp(photo.date / 1000).strftime('%Y-%m-%d\n%H:%M:%S')
            self.date_label = QLabel(date_str)
            self.date_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            text_layout.addWidget(self.name_label)
            text_layout.addWidget(self.date_label)

            layout.addLayout(text_layout)
            self.setMinimumHeight(140)

    def __init__(self, device_manager: DeviceManager):
        super().__init__()
        self.device_manager = device_manager
        self.current_device = None
        self.photo_data: List[PhotoInfo] = []
        self.loaded_count = 0  # 已加载照片计数
        self.thumb_dir = 'thumbnails'
        self.photos_reader = PhotosReader(device_manager)
        self.logger = logging.getLogger('PhotosTab')

        self.thread_pool = QThreadPool()

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
        
        # 添加刷新间隔设置（类似联系人标签页）
        self.refresh_interval_input = QLineEdit()
        self.refresh_interval_input.setPlaceholderText('自动刷新间隔（秒），0为关闭')
        self.refresh_interval_input.setFixedWidth(150)
        self.refresh_interval_input.setText("30")  # 默认30秒
        
        self.set_refresh_interval_button = QPushButton('设置自动刷新')
        self.set_refresh_interval_button.clicked.connect(self.set_refresh_interval)
        
        self.export_button = QPushButton('导出选中')
        self.export_button.clicked.connect(self.export_selected_photos)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.refresh_interval_input)
        button_layout.addWidget(self.set_refresh_interval_button)
        button_layout.addWidget(self.export_button)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()

        # 照片列表 - 改为列表模式，使用自定义控件
        self.photo_list = QListWidget()
        self.photo_list.setViewMode(QListWidget.ListMode)  # 列表模式
        self.photo_list.setSelectionMode(QListWidget.MultiSelection)
        self.photo_list.setSpacing(5)
        self.photo_list.setStyleSheet("""
            QListWidget::item {
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 5px;
                margin: 4px;
                background-color: #fafafa;
            }
            QListWidget::item:selected {
                border: 2px solid #3399ff;
                background-color: #d6eaff;
            }
        """)
        self.photo_list.itemClicked.connect(self.on_photo_selected)

        self.photo_list.verticalScrollBar().valueChanged.connect(self.on_scroll)

        # 大图预览 QLabel
        self.photo_preview = QLabel()
        self.photo_preview.setAlignment(Qt.AlignCenter)
        self.photo_preview.setMinimumSize(400, 400)
        self.photo_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.photo_preview.setText("请选择左侧照片查看预览")

        # 状态标签
        self.status_label = QLabel()

        # 左右分栏
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
            scaled_pixmap = pixmap.scaled(
                self.photo_preview.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.photo_preview.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
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
            match = (text in filename) or (text in date_str)
            item.setHidden(not match)

    def load_photos(self):
        if not self.current_device:
            QMessageBox.warning(self, "警告", "未连接设备，无法加载照片")
            return

        self.photo_list.clear()
        self.photo_data = []
        self.loaded_count = 0

        try:
            self.photo_data = self.photos_reader.scan_photos(self.current_device)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载照片失败: {e}")
            return

        self.status_label.setText(f"共发现 {len(self.photo_data)} 张照片")
        self.load_next_page()

    def load_next_page(self):
        start = self.loaded_count
        end = min(start + self.PAGE_SIZE, len(self.photo_data))

        for i in range(start, end):
            photo = self.photo_data[i]
            item = QListWidgetItem()
            item.setData(Qt.UserRole, photo)
            item.setSizeHint(QSize(0, 140))  # 控制item高度，宽度自适应

            self.photo_list.addItem(item)

            # 先放一个空白widget
            widget = self.PhotoItemWidget(photo)
            self.photo_list.setItemWidget(item, widget)

            # 异步加载缩略图，回调更新widget
            def update_thumb(icon, widget=widget):
                pixmap = icon.pixmap(128, 128)
                widget.thumb_label.setPixmap(pixmap)

            loader = ThumbLoader(photo, item, self.photos_reader, self.current_device, self.thumb_dir)
            loader.signals.finished.connect(lambda item_, icon, w=widget: update_thumb(icon, w))
            self.thread_pool.start(loader)

        self.loaded_count = end

    def on_scroll(self, value):
        scrollbar = self.photo_list.verticalScrollBar()
        if value >= scrollbar.maximum() - 50:
            if self.loaded_count < len(self.photo_data):
                self.load_next_page()

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

    def update_refresh_interval(self, value):
        """更新刷新间隔"""
        # 这个方法现在由SpinBox调用，但我们使用文本输入框方式
        pass

    def set_refresh_interval(self):
        """设置自动刷新间隔"""
        text = self.refresh_interval_input.text().strip()
        try:
            interval_sec = int(text)
            if interval_sec < 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, '输入错误', '请输入一个非负整数秒数')
            return

        self.refresh_interval = interval_sec * 1000
        if self.refresh_interval > 0:
            if self.current_device:  # 只有在设备连接时才启动定时器
                self.refresh_timer.start(self.refresh_interval)
            self.logger.info(f"设置自动刷新间隔为 {interval_sec} 秒")
        else:
            self.refresh_timer.stop()
            self.logger.info("关闭自动刷新")

    def on_device_connected(self, device_id: str):
        self.current_device = device_id
        self.refresh_button.setEnabled(True)
        self.status_label.setText(f"设备已连接: {device_id}")

    def on_device_disconnected(self):
        self.current_device = None
        self.refresh_button.setEnabled(False)
        self.photo_list.clear()
        self.photo_data.clear()
        self.status_label.setText("设备已断开，无法加载照片")
        self.photo_preview.clear()
        self.photo_preview.setText("请选择左侧照片查看预览")
