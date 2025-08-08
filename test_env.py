import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import Qt
from PIL import Image

def test_environment():
    # 测试PyQt5
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle('环境测试')
    window.setGeometry(100, 100, 300, 200)
    
    label = QLabel('环境配置正常!', window)
    label.setAlignment(Qt.AlignCenter)
    window.setCentralWidget(label)
    
    print("PyQt5初始化成功")
    
    # 测试Pillow
    try:
        # 创建一个简单的测试图像
        img = Image.new('RGB', (100, 100), color = 'red')
        print("Pillow图像处理库测试成功")
    except Exception as e:
        print(f"Pillow测试失败: {str(e)}")
    
    # 测试ADB
    import subprocess
    try:
        # 在Windows上运行adb.exe时添加CREATE_NO_WINDOW标志以避免控制台窗口闪烁
        if sys.platform == "win32":
            # Windows平台，添加CREATE_NO_WINDOW标志
            creation_flags = subprocess.CREATE_NO_WINDOW
        else:
            creation_flags = 0
            
        result = subprocess.run(['adb', 'version'], capture_output=True, text=True, timeout=10,
                               creationflags=creation_flags)
        if result.returncode == 0:
            print("ADB工具测试成功")
            print(result.stdout.strip())
        else:
            print("ADB工具测试失败")
    except Exception as e:
        print(f"ADB测试失败: {str(e)}")
    
    window.show()
    return app.exec_()

if __name__ == '__main__':
    test_environment()
