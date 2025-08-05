安卓手机数据读取软件项目文档

1. 项目结构
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
├── LICENSE                      # MIT许可证
└── README.md                    # 项目说明

2. 开发环境配置
2.1 环境要求
- IDE: Visual Studio Code 1.80+
  - 必需插件：Python、Pylance、GitLens
  - 推荐插件：Python Test Explorer、Python Docstring Generator
- 嵌入式Python 3.9.13 (选择原因：稳定性和兼容性最佳，支持所有依赖库)
- ADB工具 (Platform Tools 34.0.1+)
- Git 2.30+

2.2 环境配置步骤
1) IDE配置
   VS Code配置文件(.vscode/settings.json)包含：
   - Python解释器路径
   - 代码风格设置(PEP8)
   - 调试配置
   - 测试运行器设置

2) 一键环境配置
Windows:
```powershell
# 在项目根目录执行
.\dev_env\setup_env.bat
```
setup_env.bat 将自动：
- 配置环境变量
- 安装必要驱动
- 创建Python虚拟环境
- 初始化开发配置

macOS/Linux:
```bash
# 在项目根目录执行
chmod +x dev_env/setup_env.sh
./dev_env/setup_env.sh
```
setup_env.sh 将自动：
- 配置环境变量
- 设置USB权限
- 创建Python虚拟环境
- 初始化开发配置

3) Python依赖安装
使用项目内置Python（推荐）：
```bash
# Windows
dev_env/python-3.9.13/windows/python.exe -m pip install -r requirements.txt

# macOS/Linux
./dev_env/python-3.9.13/linux/bin/python3 -m pip install -r requirements.txt
```

使用系统Python（确保版本兼容）：
```bash
pip install -r requirements.txt
```

4) 验证安装
运行自动化检查脚本：
```bash
python scripts/verify_env.py
```

3. 需求规格说明书
3.1 功能需求
1) 设备连接管理
   - 自动检测USB连接的安卓设备
   - 支持ADB和MTP双模式切换
   - 设备信息显示（型号、安卓版本）

2) 通讯录读取
   - 读取联系人姓名、电话、邮箱
   - 支持分组和搜索
   - 联系人详情展示

3) 短信管理
   - 读取收件箱/发件箱
   - 按会话分组展示
   - 关键词搜索
   - 显示时间戳和状态

4) 相册管理
   - 读取相册图片和视频
   - 按文件夹分类
   - 缩略图预览
   - 全屏查看模式

5) 用户界面
   - 三栏式布局
   - 响应式设计
   - 中英文切换
   - 明暗主题

3.2 非功能需求
1) 兼容性
   - 操作系统: Win10/11, macOS 10.15+, Ubuntu 18.04+
   - 安卓版本: 8.0(Oreo)及以上
   - 手机品牌: 华为/小米/三星/OPPO/vivo等

2) 性能指标
   - 通讯录加载: <3s (1000条)
   - 短信加载: <5s (5000条)
   - 图片缩略图: <2s (100张)

3) 安全性
   - 数据安全
     * 本地数据使用AES-256-GCM加密存储
     * 加密密钥使用系统钥匙串管理
     * 临时文件使用安全擦除方式清理
   - 隐私保护
     * 完全离线运行，无云端传输
     * 最小权限原则请求设备权限
     * 用户数据匿名化处理
   - 日志安全
     * 敏感信息自动脱敏
     * 日志文件加密存储
     * 定期清理策略

4) 可靠性
   - 断线自动重连
   - 错误恢复机制
   - 操作日志记录

4. 开发里程碑
阶段          时间       交付物
需求分析      第1周       需求规格说明书
技术设计      第2周       系统架构设计文档
核心模块开发  第3-5周     设备管理、数据读取模块
UI开发       第6-7周     完整界面实现
兼容性测试    第8周       设备兼容性报告
性能优化      第9周       性能测试报告
用户测试      第10周      用户反馈报告
正式发布      第11周      可执行安装包

4.1 版本管理规范
- 版本号格式：主版本.次版本.修订号（如1.2.3）
- 遵循语义化版本（Semantic Versioning）
- 每个版本必须有详细的CHANGELOG.md记录

4.2 部署流程
1) 准备阶段
   - 运行完整测试套件
   - 更新版本号和更新日志
   - 生成API文档

2) 构建阶段
   ```bash
   python scripts/build_release.py --version=X.Y.Z
   ```
   - 自动化构建流程
   - 代码签名和完整性校验
   - 生成安装包和便携版

3) 发布阶段
   - 发布到GitHub Releases
   - 更新下载页面
   - 推送更新通知

4.3 升级和回滚
- 支持在线升级检查
- 保留上一版本备份
- 提供回滚脚本
- 自动备份用户数据和配置

4.4 错误处理和日志
1) 错误处理策略
   - 设备连接错误自动重试
   - 数据读取失败优雅降级
   - 异常状态自动恢复
   - 用户友好的错误提示

2) 日志系统
   - 位置：logs/app.log
   - 格式：JSON结构化日志
   - 级别：ERROR, WARNING, INFO, DEBUG
   - 自动轮转：按大小和时间
   
3) 故障排查
   - 内置诊断工具（tools/diagnostic.py）
   - 问题重现脚本生成
   - 日志分析工具
   - 常见问题解决方案

5. 测试计划
5.1 自动化测试
1) 单元测试
   - 使用pytest框架
   - 测试文件命名：test_*.py
   - 运行方式：pytest tests/unit/
   - 覆盖率目标：>90%
   - 模拟设备响应使用pytest-mock

2) 集成测试
   - 测试文件位置：tests/integration/
   - 完整工作流测试
   - 模块间接口测试
   - 真机测试用例

3) 性能测试
   - 位置：tests/performance/
   - 基准测试（benchmarks）
   - 负载测试（多设备）
   - 内存泄漏检测
   - 响应时间监控

5.2 测试数据准备
1) 测试数据集
   - 标准数据集（基本功能）
   - 边界数据集（极限情况）
   - 错误数据集（异常处理）
   - 真实数据备份（可选）

2) 测试设备池
基础设备：
- 华为：Mate 40 Pro(鸿蒙)、P30(Android)
- 小米：Mi 11、Redmi Note 9
- 三星：S21、A52
- OPPO：Find X3、Reno 6
- vivo：X60、Y70
Android版本覆盖：
- Android 8.0 (Oreo)
- Android 9.0 (Pie)
- Android 10
- Android 11
- Android 12
- Android 13
测试平台：
- Windows 11 Pro/Home
- macOS Ventura/Monterey
- Ubuntu 22.04/20.04

5.3 测试执行
1) 持续集成
   - 每次提交运行单元测试
   - 每日运行完整测试套件
   - 周末进行压力测试

2) 发布测试
   - 冒烟测试
   - 回归测试
   - 兼容性测试
   - 用户验收测试

3) 测试报告
   - 自动生成HTML报告
   - 包含测试覆盖率
   - 性能测试图表
   - 错误分析和趋势

6. 依赖管理
6.1 运行时依赖
- Python >= 3.9, < 3.10
- PyQt5 == 5.15.9
  - 原因：最后一个支持Python 3.9的稳定版本
  - 安装注意：Windows需预安装Visual C++ Runtime
- ADB工具集 >= 34.0.1
  - 用途：设备通信和调试
  - 安装位置：dev_env/adb/
- libmtp >= 1.1.17
  - 用途：MTP模式文件传输
  - Windows：包含在项目内
  - Linux：需安装libmtp-dev包
- Pillow >= 9.5.0
  - 用途：图片处理和缩略图生成
  - 依赖：libjpeg, zlib

6.2 开发依赖
- pytest >= 7.4.0：单元测试框架
- black == 23.7.0：代码格式化
- pylint >= 2.17.5：代码质量检查
- mypy >= 1.5.1：类型检查
- coverage >= 7.3.0：测试覆盖率分析

6.3 依赖版本锁定
- 项目使用 pip-tools 管理依赖
- requirements.txt：运行时依赖（锁定版本）
- requirements-dev.txt：开发依赖（锁定版本）
- requirements.in：源依赖声明
- 更新依赖：运行 scripts/update_deps.py