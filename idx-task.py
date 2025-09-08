import sys
import os
import asyncio
import logging
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

# 配置参数
URL_INDEX = 'https://idx.google.com/'

# 每个 URL 配置：检查地址、打开地址、轮询间隔（单位：秒）
URL_CONFIGS = [
    {
        'check_url': 'idx外部地址1',
        'open_url': 'https://idx.google.com/xray-keep-55221223',
        'interval': 600  # 每 5 分钟检查一次
    },
    {
        'check_url': 'idx外部地址2',
        'open_url': 'https://idx.google.com/vpn-2-59362180',
        'interval': 120  # 每 1 分钟检查一次
    },
    # 可以继续添加更多配置项
]

MONITOR_INTERVAL = 10  # 浏览器任务中的 curl 检测间隔

async def check_url_loop(config):
    check_url = config['check_url']
    open_url = config['open_url']
    interval = config['interval']

    while True:
        proc = await asyncio.create_subprocess_exec(
            'curl', '-I', check_url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode()

        first_line = output.split('\n', 1)[0].rstrip('\r\n') if output else "No output"
        logger.info(f"{check_url} 返回 {first_line}")

        if "HTTP/2 200" not in output:
            logger.info(f"✅ 创建浏览器打开指定页面 [{open_url}]")
            await handle_browser_task(check_url, open_url)

        await asyncio.sleep(interval)


async def handle_browser_task(check_url, open_url):
    co = ChromiumOptions().headless()
    co.set_paths(browser_path='/var/lib/snapd/snap/bin/chromium')
    co.set_user_data_path('./Default')
    co.set_proxy('http://192.168.200.14:10888')
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36')

    browser = Chromium(co)
    tab = browser.latest_tab

    #打开主页
    tab.get(URL_INDEX)
    
    #查找登录后的页面关键字 找到说明登录成功 登录成功后打开项目
    ele = tab.ele('xpath://*[contains(text(), "xray-keep")]', timeout=30)

    if 'xray-keep' in tab.html:
        logger.info('✅ 找到[xray-keep]')
        logger.info('⏳ 等待 5 秒后打开页面...')
        await asyncio.sleep(5)
        tab.get(open_url)
        logger.info(f'🚀 正在打开页面 {open_url}...')

        stop_event = asyncio.Event()

        async def monitor_http_status():
            while not stop_event.is_set():
                proc = await asyncio.create_subprocess_exec(
                    'curl', '-I', check_url,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await proc.communicate()
                output = stdout.decode()

                first_line = output.split('\n', 1)[0].rstrip('\r\n') if output else "No output"
                logger.info(f"[monitor] {check_url} {first_line}")

                if "HTTP/2 200" in output:
                    logger.info("🟢 curl 检测到 HTTP/2 200，10 秒后关闭浏览器释放资源")
                    stop_event.set()
                    await asyncio.sleep(10)
                    browser.quit()
                    logger.info("🧹 尝试清理残留的 chromium 进程...")
                    os.system("pkill -f chromium 2>/dev/null")
                    logger.info("✅ 浏览器已关闭")
                    return

                await asyncio.sleep(MONITOR_INTERVAL)

        monitor_task = asyncio.create_task(monitor_http_status())

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=250)
        except asyncio.TimeoutError:
            logger.info('🔄 已过4分钟，刷新页面...')
            tab.refresh()
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=120)
            except asyncio.TimeoutError:
                logger.info("⏳ 页面已打开额外 100 秒，关闭浏览器")
                browser.quit()
                logger.info("🧹 尝试清理残留的 chromium 进程...")
                os.system("pkill -f chromium")
                logger.info("✅ 浏览器已关闭（超时）")

    else:
        logger.warning('❌ 没有找到[xray-keep]')
        browser.quit()
        logger.info("🧹 尝试清理残留的 chromium 进程...")
        os.system("pkill -f chromium")
        logger.info("✅ 浏览器已关闭（未找到关键字）")



async def main():
    tasks = [check_url_loop(config) for config in URL_CONFIGS]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
