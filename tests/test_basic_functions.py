import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.device_manager import DeviceManager
from src.core.contacts_reader import ContactsReader
from src.core.sms_reader import SMSReader
from src.core.photos_reader import PhotosReader
from src.core.permissions import PermissionManager

def test_device_connection():
    """测试设备连接"""
    print("\n1. 测试设备连接...")
    device_manager = DeviceManager()
    devices = device_manager.get_devices()
    
    if devices:
        print(f"✓ 已连接设备: {devices}")
        device_info = device_manager.get_device_info()
        print("设备信息:")
        for key, value in device_info.items():
            print(f"  {key}: {value}")
    else:
        print("✗ 未检测到设备")
    return bool(devices)

def test_permissions(device_manager):
    """测试权限管理"""
    print("\n2. 测试权限管理...")
    permission_manager = PermissionManager(device_manager)
    permissions = permission_manager.check_all_permissions()
    
    print("权限状态:")
    for permission, granted in permissions.items():
        status = "✓" if granted else "✗"
        print(f"  {status} {permission}")
    
    if not permission_manager.has_all_permissions():
        print("\n请求缺失权限...")
        permission_manager.request_all_permissions()
    
    return permission_manager.has_all_permissions()

def test_contacts_reader(device_manager):
    """测试通讯录读取"""
    print("\n3. 测试通讯录读取...")
    contacts_reader = ContactsReader(device_manager)
    
    # 读取所有联系人
    contacts = contacts_reader.get_all_contacts()
    if contacts:
        print(f"✓ 成功读取 {len(contacts)} 个联系人")
        print("第一个联系人示例:")
        print(contacts[0].to_dict())
    else:
        print("✗ 未读取到联系人")
    
    # 测试保存和加载
    test_file = "test_contacts.json"
    contacts_reader.save_contacts(contacts, test_file)
    loaded_contacts = contacts_reader.load_contacts(test_file)
    if loaded_contacts:
        print(f"✓ 成功保存和加载联系人数据")
    
    # 清理测试文件
    if os.path.exists(test_file):
        os.remove(test_file)
    
    return bool(contacts)

def test_sms_reader(device_manager):
    """测试短信读取"""
    print("\n4. 测试短信读取...")
    sms_reader = SMSReader(device_manager)
    
    # 读取所有短信
    messages = sms_reader.get_all_sms()
    if messages:
        print(f"✓ 成功读取 {len(messages)} 条短信")
        print("第一条短信示例:")
        print(messages[0].to_dict())
    else:
        print("✗ 未读取到短信")
    
    # 测试会话分组
    conversations = sms_reader.get_conversations()
    if conversations:
        print(f"✓ 成功获取 {len(conversations)} 个会话")
    
    return bool(messages)

def test_photos_reader(device_manager):
    """测试照片读取"""
    print("\n5. 测试照片读取...")
    photos_reader = PhotosReader(device_manager)
    
    # 扫描照片
    photos = photos_reader.scan_photos()
    if photos:
        print(f"✓ 成功扫描到 {len(photos)} 张照片")
        print("第一张照片信息:")
        print(photos[0].to_dict())
        
        # 测试缩略图生成
        test_dir = "test_photos"
        os.makedirs(test_dir, exist_ok=True)
        
        photo = photos[0]
        local_path = photos_reader.download_photo(photo, test_dir)
        if local_path:
            print(f"✓ 成功下载照片到 {local_path}")
            
            thumb_path = photos_reader.create_thumbnail(local_path)
            if thumb_path:
                print(f"✓ 成功生成缩略图 {thumb_path}")
                
        # 清理测试文件
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)
    else:
        print("✗ 未扫描到照片")
    
    return bool(photos)

def main():
    """主测试流程"""
    print("=== Android数据读取功能测试 ===")
    
    # 1. 测试设备连接
    if not test_device_connection():
        print("\n请连接Android设备后重试")
        return
    
    # 创建设备管理器实例
    device_manager = DeviceManager()
    
    # 2. 测试权限管理
    if not test_permissions(device_manager):
        print("\n请确保已授予所需权限")
        return
    
    # 3. 测试通讯录读取
    contacts_result = test_contacts_reader(device_manager)
    
    # 4. 测试短信读取
    sms_result = test_sms_reader(device_manager)
    
    # 5. 测试照片读取
    photos_result = test_photos_reader(device_manager)
    
    # 总结测试结果
    print("\n=== 测试结果汇总 ===")
    print(f"通讯录读取: {'✓' if contacts_result else '✗'}")
    print(f"短信读取: {'✓' if sms_result else '✗'}")
    print(f"照片读取: {'✓' if photos_result else '✗'}")

if __name__ == '__main__':
    main()
