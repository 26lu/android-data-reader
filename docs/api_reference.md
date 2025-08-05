# API参考文档

## 1. 核心模块API

### 1.1 DeviceManager（设备管理器）

#### 类定义
```python
class DeviceManager:
    def __init__(self):
        pass
```

#### 方法

##### get_devices()
获取连接的设备列表

**参数:** 无

**返回值:** 
- List[str]: 设备序列号列表

##### get_device_info(device_id: str)
获取设备信息

**参数:**
- device_id (str): 设备序列号

**返回值:**
- Dict[str, str]: 设备信息字典，包含型号、Android版本等

##### get_device_permissions(device_id: str)
检查设备权限

**参数:**
- device_id (str): 设备序列号

**返回值:**
- Dict[str, bool]: 权限状态字典

### 1.2 ContactsReader（通讯录读取器）

#### 类定义
```python
class ContactsReader:
    def __init__(self, device_manager: DeviceManager):
        pass
```

#### 方法

##### get_all_contacts()
获取所有联系人

**参数:** 无

**返回值:**
- List[Contact]: 联系人对象列表

### 1.3 SMSReader（短信读取器）

#### 类定义
```python
class SMSReader:
    def __init__(self, device_manager: DeviceManager):
        pass
```

#### 方法

##### get_all_sms()
获取所有短信

**参数:** 无

**返回值:**
- List[SMSMessage]: 短信对象列表

##### get_conversations()
获取会话分组

**参数:** 无

**返回值:**
- Dict[str, List[SMSMessage]]: 按地址分组的会话字典

### 1.4 PhotosReader（照片读取器）

#### 类定义
```python
class PhotosReader:
    def __init__(self, device_manager: DeviceManager):
        pass
```

#### 方法

##### scan_photos()
扫描照片

**参数:** 无

**返回值:**
- List[Photo]: 照片对象列表

##### download_photo(photo: Photo, save_dir: str)
下载照片

**参数:**
- photo (Photo): 照片对象
- save_dir (str): 保存目录

**返回值:**
- str: 本地文件路径

## 2. UI模块API

### 2.1 MainWindow（主窗口）

#### 类定义
```python
class MainWindow(QMainWindow):
    def __init__(self):
        pass
```

### 2.2 ContactsTab（通讯录标签页）

#### 类定义
```python
class ContactsTab(QWidget):
    def __init__(self, device_manager: DeviceManager):
        pass
```

### 2.3 SMSTab（短信标签页）

#### 类定义
```python
class SMSTab(QWidget):
    def __init__(self, device_manager: DeviceManager):
        pass
```

### 2.4 PhotosTab（照片标签页）

#### 类定义
```python
class PhotosTab(QWidget):
    def __init__(self, device_manager: DeviceManager):
        pass
```