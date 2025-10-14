#!/bin/sh

# 添加时间戳的函数
timestamp() {
    # 获取当前UTC时间戳，加上8小时（28800秒）
    local current_timestamp=$(date +%s)
    local beijing_timestamp=$((current_timestamp + 28800))
    echo "[$(date -u -d "@$beijing_timestamp" '+%Y-%m-%d %H:%M:%S')] - INFO - ✅"
}

cleanup() {
    echo "$(timestamp) 清理Xvfb进程..."
    pkill -f "Xvfb :99"
}

# 设置信号处理，确保脚本退出时清理Xvfb
trap cleanup EXIT INT TERM

# 检查Xvfb是否已经在运行
if pgrep -f "Xvfb :99" > /dev/null; then
    echo "$(timestamp) Xvfb :99已经在运行了"
    export DISPLAY=:99
    python3 lunes.py
else
    # 启动虚拟显示服务器
    echo "$(timestamp) 启动Xvfb..."
    Xvfb :99 -screen 0 1024x768x24 &
    sleep 2
    export DISPLAY=:99
    python3 lunes.py
fi
