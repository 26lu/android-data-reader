from typing import List, Dict, Optional
import logging
from .device_manager import DeviceManager

class PermissionManager:
    PERMISSIONS = {
        'READ_CONTACTS': 'android.permission.READ_CONTACTS',
        'READ_SMS': 'android.permission.READ_SMS',
        'READ_EXTERNAL_STORAGE': 'android.permission.READ_EXTERNAL_STORAGE',
        'WRITE_EXTERNAL_STORAGE': 'android.permission.WRITE_EXTERNAL_STORAGE'
    }

    def __init__(self, device_manager: DeviceManager):
        """初始化权限管理器

        Args:
            device_manager: 设备管理器实例
        """
        self.device_manager = device_manager
        self._setup_logging()

    def _setup_logging(self):
        """配置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename='logs/permissions.log'
        )
        self.logger = logging.getLogger('PermissionManager')

    def check_permission(self, permission: str,
                        device_id: Optional[str] = None) -> bool:
        """检查单个权限状态

        Args:
            permission: 权限名称
            device_id: 设备ID

        Returns:
            是否已授权
        """
        if permission not in self.PERMISSIONS:
            self.logger.error(f"未知权限: {permission}")
            return False

        android_permission = self.PERMISSIONS[permission]
        device_arg = ['-s', device_id] if device_id else []

        # 检查应用权限状态
        args = ['shell', 'pm', 'list', 'permissions', '-g', '-d']
        success, output = self.device_manager._run_adb_command(args, device_id)


        return success and android_permission in output

    def check_all_permissions(self,
                            device_id: Optional[str] = None) -> Dict[str, bool]:
        """检查所有所需权限的状态

        Args:
            device_id: 设备ID

        Returns:
            权限状态字典
        """
        return {
            name: self.check_permission(name, device_id)
            for name in self.PERMISSIONS
        }

    def request_permission(self, permission: str,
                         device_id: Optional[str] = None) -> bool:
        """请求授予权限

        Args:
            permission: 权限名称
            device_id: 设备ID

        Returns:
            是否成功请求权限
        """
        if permission not in self.PERMISSIONS:
            self.logger.error(f"未知权限: {permission}")
            return False

        android_permission = self.PERMISSIONS[permission]
        device_arg = ['-s', device_id] if device_id else []

        # 尝试授予权限
        args = ['shell', 'pm', 'grant', 'com.android.reader', android_permission]
        success, _ = self.device_manager._run_adb_command(args, device_id)


        if success:
            self.logger.info(f"成功请求权限: {permission}")
        else:
            self.logger.error(f"请求权限失败: {permission}")

        return success

    def request_all_permissions(self,
                              device_id: Optional[str] = None) -> Dict[str, bool]:
        """请求所有所需权限

        Args:
            device_id: 设备ID

        Returns:
            权限请求结果字典
        """
        results = {}
        for permission in self.PERMISSIONS:
            results[permission] = self.request_permission(permission, device_id)
        return results

    def get_missing_permissions(self,
                              device_id: Optional[str] = None) -> List[str]:
        """获取缺失的权限列表

        Args:
            device_id: 设备ID

        Returns:
            缺失权限名称列表
        """
        status = self.check_all_permissions(device_id)
        return [name for name, granted in status.items() if not granted]

    def has_all_permissions(self, device_id: Optional[str] = None) -> bool:
        """检查是否已获得所有所需权限

        Args:
            device_id: 设备ID

        Returns:
            是否已获得所有权限
        """
        return len(self.get_missing_permissions(device_id)) == 0
