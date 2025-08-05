安卓手机数据读取软件项目文档

## 1. 项目简介

Android数据读取器是一款跨平台工具，可帮助用户从Android设备中提取通讯录、短信和照片数据。本软件支持Windows、macOS和Linux操作系统。

### 核心功能
- 设备连接管理: 自动检测USB连接的安卓设备，支持ADB和MTP双模式切换
- 通讯录读取: 读取联系人姓名、电话、邮箱，支持分组和搜索
- 短信管理: 读取收件箱/发件箱，按会话分组展示，支持关键词搜索
- 相册管理: 读取相册图片和视频，按文件夹分类，支持缩略图预览
- 用户界面: 三栏式布局，响应式设计，支持中英文切换和明暗主题

## 2. 项目结构

```
android-data-reader/
├── .vscode/                     # VS Code配置
│   └── settings.json            # 编辑器设置
│
├── dev_env/                     # 开发环境
│   ├── adb/                     # ADB工具
│   │   ├── adb.exe              # Windows版
│   │   ├── adb_mac              # macOS版
│   │   └── adb_linux            # Linux版
│   │
│   ├── python-3.9.13/           # 嵌入式Python
│   │   ├── windows/             # Windows版
│   │   ├── macos/               # macOS版
│   │   └── linux/               # Linux版
│   │
│   └── setup_env.sh             # 环境配置脚本
│
├── docs/                        # 项目文档
│   ├── requirements.md          # 需求规格说明书
│   ├── design_document.md       # 设计文档
│   ├── api_reference.md         # API参考
│   ├── test_plan.md             # 测试计划
│   └── user_manual.md           # 用户手册
│
├── src/                         # 源代码
│   ├── core/                    # 核心业务逻辑
│   │   ├── device_manager.py    # 设备管理
│   │   ├── contacts_reader.py   # 通讯录读取
│   │   ├── sms_reader.py        # 短信读取
│   │   ├── photos_reader.py     # 相册读取
│   │   └── permissions.py       # 权限管理
│   │
│   ├── ui/                      # 用户界面
│   │   ├── main_window.py       # 主窗口
│   │   ├── contacts_tab.py      # 通讯录标签页
│   │   ├── sms_tab.py           # 短信标签页
│   │   └── photos_tab.py        # 相册标签页
│   │
│   ├── drivers/                 # 设备驱动
│   │   ├── universal_adb_driver.exe
│   │   └── mtp_driver.dll
│   │
│   ├── resources/               # 资源文件
│   │   ├── icons/               # 应用图标
│   │   ├── vendor_profiles/     # 厂商配置
│   │   └── styles.qss           # 界面样式
│   │
│   └── main.py                  # 应用入口
│
├── tests/                       # 测试代码
│   ├── unit/                    # 单元测试
│   │   ├── test_device_manager.py
│   │   └── test_contacts_reader.py
│   │
│   └── integration/             # 集成测试
│       ├── test_full_workflow.py
│       └── device_compatibility/
│
├── scripts/                     # 实用脚本
│   ├── install_drivers.bat      # Windows驱动安装
│   ├── install_drivers.sh       # Linux/macOS驱动安装
│   └── build_release.py         # 发布构建脚本
│
├── .gitignore                   # Git忽略规则
├── requirements.txt             # Python依赖
├── requirements-dev.txt         # Python开发依赖
├── LICENSE                      # MIT许可证
└── README.md                    # 项目说明
```

## 3. 开发环境配置

项目已包含完整的开发环境：
- 嵌入式Python 3.9.13 (Windows/macOS/Linux)
- ADB工具 (各平台版本)
- 必要驱动文件

### 一键环境配置

Windows:
```bash
# 在项目根目录执行
.\dev_env\setup_env.bat
```

macOS/Linux:
```bash
# 在项目根目录执行
chmod +x dev_env/setup_env.sh
./dev_env/setup_env.sh
```

### Python依赖安装

使用项目内置Python:
```bash
dev_env/python-3.9.13/windows/python.exe -m pip install -r requirements.txt
```

或使用系统Python:
```bash
pip install -r requirements.txt
```

开发环境依赖安装:
```bash
pip install -r requirements-dev.txt
```

## 4. 运行项目

### 开发环境运行
```bash
python -m src.main
```

### 安装后运行
```bash
pip install .
android-reader
```

## 5. 构建可执行文件

使用PyInstaller构建独立可执行文件:
```bash
pip install pyinstaller
pyinstaller --onefile src/main.py
```

## 6. 测试

### 运行单元测试
```bash
pytest tests/unit/
```

### 运行集成测试
```bash
pytest tests/integration/
```

### 运行全部测试
```bash
pytest
```

## 7. 文档

项目文档位于 [docs/](file:///d:/vscode/code/python/android-data-reader/docs/) 目录中:
- [需求规格说明书](file:///d:/vscode/code/python/android-data-reader/docs/requirements.md)
- [设计文档](file:///d:/vscode/code/python/android-data-reader/docs/design_document.md)
- [API参考](file:///d:/vscode/code/python/android-data-reader/docs/api_reference.md)
- [测试计划](file:///d:/vscode/code/python/android-data-reader/docs/test_plan.md)
- [用户手册](file:///d:/vscode/code/python/android-data-reader/docs/user_manual.md)

## 8. 贡献

欢迎提交Issue和Pull Request来改进项目。

## 9. 许可证

本项目采用MIT许可证，详情请见 [LICENSE](file:///d:/vscode/code/python/android-data-reader/LICENSE) 文件。