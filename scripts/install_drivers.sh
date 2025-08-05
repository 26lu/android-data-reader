#!/bin/bash
# Linux/macOS环境配置脚本

# 设置环境变量
export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PROJECT_ROOT/dev_env/adb:$PATH"
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# 设置USB权限
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="*", MODE="0666"' | sudo tee /etc/udev/rules.d/51-android.rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# 创建Python虚拟环境
echo "Creating Python virtual environment..."
python3 -m venv "$PROJECT_ROOT/venv"
source "$PROJECT_ROOT/venv/bin/activate"

# 安装依赖
echo "Installing dependencies..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    brew install libmtp
else
    # Linux
    sudo apt-get update
    sudo apt-get install -y libmtp-dev libjpeg-dev zlib1g-dev
fi

pip install -r "$PROJECT_ROOT/requirements.txt"
pip install -r "$PROJECT_ROOT/requirements-dev.txt"

# 初始化配置
echo "Initializing configuration..."
python "$PROJECT_ROOT/scripts/verify_env.py"

echo "Setup completed successfully!"
