#!/usr/bin/env python3
"""
将Android数据读取器打包为带时效限制的Windows可执行文件的脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

def check_pyinstaller():
    """检查PyInstaller是否已安装"""
    try:
        import PyInstaller
        print("✅ PyInstaller已安装")
        return True
    except ImportError:
        print("❌ PyInstaller未安装")
        return False

def install_pyinstaller():
    """安装PyInstaller"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller安装成功")
        return True
    except subprocess.CalledProcessError:
        print("❌ PyInstaller安装失败")
        return False

def update_main_py_with_date():
    """更新主程序中的构建日期"""
    main_py_path = Path(__file__).parent.parent / "src" / "main.py"

    if not main_py_path.exists():
        print(f"❌ 主程序文件不存在: {main_py_path}")
        return False

    try:
        # 读取文件内容
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 获取当前日期
        current_date = datetime.now().strftime("%Y-%m-%d")

        # 替换构建日期
        updated_content = content.replace(
            'BUILD_DATE = "2025-08-06"',
            f'BUILD_DATE = "{current_date}"'
        )

        # 写回文件
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"✅ 主程序构建日期已更新为: {current_date}")
        return True
    except Exception as e:
        print(f"❌ 更新主程序构建日期失败: {e}")
        return False

def build_executable():
    """构建带时效限制的可执行文件"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    main_script = project_root / "src" / "main.py"

    if not main_script.exists():
        print(f"❌ 主程序文件不存在: {main_script}")
        return False

    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AndroidDataReader_Trial",
        "--windowed",  # GUI应用，不显示控制台窗口
        "--onefile",   # 打包成单个exe文件
        "--icon", "NONE",  # 不使用图标
        "--add-data", f"platform-tools{os.pathsep}platform-tools",  # 包含ADB工具
        "--hidden-import", "PyQt5.sip",
        "--hidden-import", "PyQt5.QtCore",
        "--hidden-import", "PyQt5.QtGui",
        "--hidden-import", "PyQt5.QtWidgets",
        str(main_script)
    ]

    print("正在构建带时效限制的可执行文件...")
    print(f"命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 可执行文件构建成功")
            return True
        else:
            print("❌ 构建失败:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ 构建过程中出现异常: {e}")
        return False

def restore_main_py():
    """恢复主程序中的构建日期为默认值"""
    main_py_path = Path(__file__).parent.parent / "src" / "main.py"

    if not main_py_path.exists():
        print(f"❌ 主程序文件不存在: {main_py_path}")
        return False

    try:
        # 读取文件内容
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 获取当前日期
        current_date = datetime.now().strftime("%Y-%m-%d")

        # 恢复默认构建日期
        updated_content = content.replace(
            f'BUILD_DATE = "{current_date}"',
            'BUILD_DATE = "2025-08-06"'
        )

        # 写回文件
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print("✅ 主程序构建日期已恢复为默认值")
        return True
    except Exception as e:
        print(f"❌ 恢复主程序构建日期失败: {e}")
        return False

def main():
    """主函数"""
    print("开始构建Android数据读取器的带时效限制Windows可执行文件...")
    print("⚠️  注意: 此版本将在100天后过期，无法继续使用")

    # 检查并安装PyInstaller
    if not check_pyinstaller():
        print("正在安装PyInstaller...")
        if not install_pyinstaller():
            return False

    # 更新主程序中的构建日期
    if not update_main_py_with_date():
        return False

    # 构建可执行文件
    build_success = build_executable()

    # 恢复主程序中的构建日期
    restore_main_py()

    if build_success:
        print("\n✨ 构建完成!")
        print("可执行文件位于 dist/AndroidDataReader_Trial.exe")
        print("⚠️  此版本将在200天后过期，无法继续使用")
        return True
    else:
        print("\n❌ 构建失败!")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
