#!/usr/bin/env python3
"""
将Android数据读取器打包为Windows可执行文件的脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

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

def build_executable():
    """构建可执行文件"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    main_script = project_root / "src" / "main.py"
    
    if not main_script.exists():
        print(f"❌ 主程序文件不存在: {main_script}")
        return False
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AndroidDataReader",
        "--windowed",  # GUI应用，不显示控制台窗口
        "--onefile",   # 打包成单个exe文件
        "--icon", "NONE",  # 不使用图标
        "--add-data", f"platform-tools{os.pathsep}platform-tools",  # 包含ADB工具
        "--hidden-import", "PyQt5.sip",
        str(main_script)
    ]
    
    print("正在构建可执行文件...")
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

def main():
    """主函数"""
    print("开始构建Android数据读取器的Windows可执行文件...")
    
    # 检查并安装PyInstaller
    if not check_pyinstaller():
        print("正在安装PyInstaller...")
        if not install_pyinstaller():
            return False
    
    # 构建可执行文件
    if build_executable():
        print("\n✨ 构建完成!")
        print("可执行文件位于 dist/AndroidDataReader.exe")
        return True
    else:
        print("\n❌ 构建失败!")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)