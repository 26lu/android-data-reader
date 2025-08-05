@echo off
REM Windows环境配置脚本

REM 设置环境变量
set PROJECT_ROOT=%~dp0..\
set PATH=%PROJECT_ROOT%dev_env\adb;%PATH%
set PYTHONPATH=%PROJECT_ROOT%src;%PYTHONPATH%

REM 安装ADB工具
echo Installing ADB tools...
set PLATFORM_TOOLS_DIR=%PROJECT_ROOT%platform-tools
if not exist "%PLATFORM_TOOLS_DIR%" (
    echo Downloading platform-tools...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile 'platform-tools.zip'}"
    echo Extracting platform-tools...
    powershell -Command "& {Expand-Archive -Path 'platform-tools.zip' -DestinationPath '%PROJECT_ROOT%' -Force}"
    del platform-tools.zip
)
set PATH=%PLATFORM_TOOLS_DIR%;%PATH%

REM 如果需要，激活虚拟环境
if exist "%PROJECT_ROOT%venv\Scripts\activate.bat" (
    call %PROJECT_ROOT%venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found. Please create a virtual environment first.
    exit /b 1
)

REM 安装依赖
echo Installing dependencies...
pip install -r %PROJECT_ROOT%requirements.txt
pip install -r %PROJECT_ROOT%requirements-dev.txt

REM 初始化配置
echo Initializing configuration...
python %PROJECT_ROOT%scripts\verify_env.py

echo Setup completed successfully!
