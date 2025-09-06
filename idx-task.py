import time
import sys
import asyncio
import logging
import threading
from flask import Flask, render_template_string
from DrissionPage import Chromium, ChromiumOptions


# 日志配置
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('./app.log')
file_handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='[%Y-%m-%d %H:%M:%S]')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# Flask 应用
app = Flask(__name__)
LOG_FILE = './app.log'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>日志查看器</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: monospace; background: #1e1e1e; color: #dcdcdc; padding: 20px; }
        h1 { color: #00ff99; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
    <h1>📜 当前日志输出</h1>
    <pre>{{ logs }}</pre>
</body>
</html>
"""

@app.route('/')
def show_logs():
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            logs = ''.join(reversed(lines))  # 最新日志在最上方
    except FileNotFoundError:
        logs = "日志文件不存在。"
    return render_template_string(HTML_TEMPLATE, logs=logs)

# 主页
URL_INDEX = 'https://idx.google.com/'
# idx.google.com 需要保活的idx项目外网地址
URL_TO_CHECK = 'https://9000-firebase-xray-keep-1752810417431.cluster-vyr53kd25jc2yvngldrwyq6zc4.cloudworkstations.dev'
# idx.google.com 需要启动的idx项目
URL_TO_OPEN = 'https://idx.google.com/xray-keep-55221223'
# 300秒检查一次
CHECK_INTERVAL = 300

async def check_url(key='xray-keep'):
    while True:
        proc = await asyncio.create_subprocess_exec(
            'curl', '-I', URL_TO_CHECK,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode()

        first_line = output.split('\n', 1)[0].rstrip('\r\n') if output else "No output"
        logger.info(f"[{key}] {first_line}")

        if "HTTP/2 200" not in output:
            logger.warning(f"[{key}] 返回 {first_line},创建浏览器打开指定页面...")
            await handle_browser_task()

        await asyncio.sleep(CHECK_INTERVAL)

async def handle_browser_task():
    co = ChromiumOptions().headless()
    co.set_paths(browser_path='/var/lib/snapd/snap/bin/chromium')
    co.set_user_data_path('./Default')
    co.set_proxy('http://192.168.200.14:10888')
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36')

    browser = Chromium(co)
    tab = browser.latest_tab

    tab.get(URL_INDEX)
    # 项目名称
    ele = tab.ele('xpath://*[contains(text(), "xray-keep")]', timeout=30)

    if 'xray-keep' in tab.html:
        logger.info('✅ 找到[xray-keep]')
        logger.info('⏳ 等待 5 秒后打开页面...')
        await asyncio.sleep(5)
        tab.get(URL_TO_OPEN)
        logger.info('🚀 正在打开页面[xray-keep]...')

        # 创建退出事件
        stop_event = asyncio.Event()

        # 启动 curl 检测任务
        async def monitor_http_status():
            while not stop_event.is_set():
                proc = await asyncio.create_subprocess_exec(
                    'curl', '-I', URL_TO_CHECK,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await proc.communicate()
                output = stdout.decode()

                first_line = output.split('\n', 1)[0].rstrip('\r\n') if output else "No output"
                logger.info(f"[monitor] {first_line}")

                if "HTTP/2 200" in output:
                    logger.info("🟢 curl 检测到 HTTP/2 200，关闭浏览器释放资源")
                    stop_event.set()
                    await asyncio.sleep(5)
                    browser.quit()
                    logger.info("✅ 浏览器已关闭")
                    return

                await asyncio.sleep(5)

        # 启动 curl 检测任务
        monitor_task = asyncio.create_task(monitor_http_status())

        # 下面是浏览器自动启动项目
        try:
            # 第一阶段：停留 240 秒
            await asyncio.wait_for(stop_event.wait(), timeout=250)
        except asyncio.TimeoutError:
            logger.info("⏳ 页面已打开 240 秒，刷新页面")
            tab.refresh()
            logger.info('🔄 已过4分钟，刷新页面...')
            try:
                # 第二阶段：再停留 100 秒
                await asyncio.wait_for(stop_event.wait(), timeout=120)
            except asyncio.TimeoutError:
                logger.info("⏳ 页面已打开额外 100 秒，关闭浏览器")
                browser.quit()
                logger.info("✅ 浏览器已关闭（超时）")

    else:
        logger.warning('❌ 没有找到[xray-keep]')
        browser.quit()
        logger.info("✅ 浏览器已关闭（未找到关键字）")


# 启动 Flask 和 asyncio 的组合
def start_flask():
    app.run(host='0.0.0.0', port=33328, debug=False)

def start_async_loop():
    asyncio.run(check_url())

if __name__ == '__main__':
    threading.Thread(target=start_flask, daemon=True).start()
    start_async_loop()
