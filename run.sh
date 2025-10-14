#!/bin/sh

# 检查Xvfb是否已经在运行
if pgrep -f "Xvfb :99" > /dev/null; then
    echo "Xvfb :99已经在运行了"
    export DISPLAY=:99
    python3 lunes.py
else
    # 启动虚拟显示服务器
    echo "启动Xvfb..."

    # 先删除文件再启动
    if [ -f "/tmp/.X99-lock" ]; then
        echo "发现残留的 /tmp/.X99-lock 文件，正在删除..."
        rm -f /tmp/.X99-lock
    fi

    Xvfb :99 -screen 0 1024x768x24 &
    sleep 2
    export DISPLAY=:99
    python3 lunes.py
fi
