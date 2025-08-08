#!/usr/bin/env python3
"""环境验证脚本"""

import sys
import os
import subprocess
import platform
from typing import List, Dict

def check_python_version() -> bool:
    """检查Python版本"""
    required_version = (3, 9)
    current_version = sys.version_info[:2]
    return current_version >= required_version

def check_dependencies() -> Dict[str, bool]:
    """检查依赖包"""
    required_packages = {
        'PyQt5': '5.15.9',
        'Pillow': '9.5.0',
        'pytest': '7.4.0',
        'black': '23.7.0',
        'pylint': '2.17.5'
    }
    
    results = {}
    for package, version in required_packages.items():
        try:
            imported = __import__(package)
            if package == 'PyQt5':
                actual_version = imported.__version__
            else:
                actual_version = imported.__version__
            # Convert version strings to tuples for comparison
            def parse_version(v):
                return tuple(map(int, v.split('.')))
            
            req_parts = parse_version(version)
            try:
                actual_parts = parse_version(actual_version)
                # Check major and minor version match exactly
                results[package] = actual_parts[:2] == req_parts[:2]
            except (ValueError, AttributeError):
                results[package] = False
        except (ImportError, AttributeError):
            results[package] = False
    return results

def check_adb() -> bool:
    """检查ADB工具"""
    try:
        # 在Windows上运行adb.exe时添加CREATE_NO_WINDOW标志以避免控制台窗口闪烁
        if sys.platform == "win32":
            # Windows平台，添加CREATE_NO_WINDOW标志
            creation_flags = subprocess.CREATE_NO_WINDOW
        else:
            creation_flags = 0
            
        subprocess.run(['adb', 'version'], capture_output=True, check=True, timeout=10,
                      creationflags=creation_flags)
        return True
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False

def main():
    """主函数"""
    all_passed = True
    
    # 检查Python版本
    if not check_python_version():
        print("❌ Python版本检查失败：需要Python 3.9或更高版本")
        all_passed = False
    else:
        print("✅ Python版本检查通过")

    # 检查依赖包
    deps_results = check_dependencies()
    for package, passed in deps_results.items():
        if not passed:
            print(f"❌ {package}检查失败")
            all_passed = False
        else:
            print(f"✅ {package}检查通过")

    # 检查ADB
    if not check_adb():
        print("❌ ADB工具检查失败")
        all_passed = False
    else:
        print("✅ ADB工具检查通过")

    # 最终结果
    if all_passed:
        print("\n✨ 所有检查均已通过！环境配置正确。")
        sys.exit(0)
    else:
        print("\n⚠️ 存在配置问题，请检查上述错误并修复。")
        sys.exit(1)

if __name__ == '__main__':
    main()
