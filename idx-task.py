import sys
import os
import asyncio
import logging
import time
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


# 每个 URL 配置：检查地址、打开地址、查找元素（关键字、项目名称）、轮询间隔（单位：秒）
URL_CONFIGS = [
    {
        'check_url': 'https://bashinfo.123.qzz.io/',
        'open_url': 'https://idx.google.com/',
        'keys': 'xray-keep',
        'interval': 600
    },
    {
        'check_url': 'https://9000-firebase-flask-keep-1773145675111.cluster-123.cloudworkstations.dev/',
        'open_url': 'https://idx.google.com/',
        'keys': 'flask-keep',
        'interval': 600
    },
    {
        'check_url': 'https://9000-firebase-console-1773678062370.cluster-123.cloudworkstations.dev/',
        'open_url': 'https://idx.google.com/',
        'keys': 'docker-info',
        'interval': 300
    },
]

MONITOR_INTERVAL = 10  # 浏览器任务中的 curl 检测间隔

async def check_url_loop(config):
    check_url = config['check_url']
    open_url = config['open_url']
    keys = config['keys']
    interval = config['interval']

    while True:
        proc = await asyncio.create_subprocess_exec(
            'curl', '-i', check_url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode()

        first_line = output.split('\n', 1)[0].rstrip('\r\n') if output else "No output"
        # logger.info(f"{check_url} 返回 {first_line}")

        if "200" not in first_line:
            logger.warning(f"{check_url} 返回 {first_line}")
            logger.warning(f"✅ 创建浏览器打开指定页面 [{open_url}][{keys}]")
            await handle_browser_task(check_url, open_url, keys)

        await asyncio.sleep(interval)


async def handle_browser_task(check_url, open_url, keys):
    co = ChromiumOptions().headless()
    co.set_paths(browser_path='/var/lib/snapd/snap/bin/chromium')
    co.set_user_data_path('./dnf')
    co.set_proxy('http://192.168.200.14:10888')
    co.set_argument('--window-size', '800,800')
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36')

    browser = None
    monitor_task = None
    
    try:
        browser = Chromium(co)
        tab = browser.new_tab()

        tab.get(open_url)
        #查找指定关键字 没有找到说明登录失败
        ele = tab.ele(f'xpath://*[contains(text(), "{keys}")]', timeout=30)

        if keys in tab.html:
            logger.info(f'✅ 在 {open_url} 找到[{keys}]')
            
            # 处理 NoRectError 的点击逻辑
            try:
                ele.click()  # 先尝试正常点击
                logger.info(f"✅ 成功点击元素")
            except Exception as e:
                # 检查异常类型字符串
                if 'NoRectError' in str(type(e)):
                    logger.info(f"⚠️ 元素无尺寸，尝试用 JavaScript 点击 [{keys}]")
                    # 使用 JavaScript 强制点击
                    tab.run_js("arguments[0].click();", ele)
                    logger.info(f"✅ JavaScript 点击成功")
                else:
                    logger.warning(f"⚠️ 其他点击异常: {e}")
                    # 备用方法：直接使用 JavaScript
                    tab.run_js("arguments[0].click();", ele)
            
            tab.wait.doc_loaded()
            logger.info(f'🚀 正在打开页面 [{open_url}][{keys}]')

            stop_event = asyncio.Event()

            async def monitor_http_status():
                while not stop_event.is_set():
                    try:
                        proc = await asyncio.create_subprocess_exec(
                            'curl', '-i', check_url,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, _ = await proc.communicate()
                        output = stdout.decode()

                        first_line = output.split('\n', 1)[0].rstrip('\r\n') if output else "No output"
                        logger.info(f"[monitor] {check_url} {first_line}")

                        if "200" in first_line:
                            logger.info(f"🟢 curl 检测到 {check_url} HTTP/2 200，10 秒后关闭浏览器释放资源")
                            stop_event.set()
                            await asyncio.sleep(10)
                            return
                    except Exception as e:
                        logger.warning(f"监控任务异常: {e}")
                    
                    await asyncio.sleep(MONITOR_INTERVAL)

            monitor_task = asyncio.create_task(monitor_http_status())

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=220)
                # 正常收到 200 后退出
                logger.info("✅ 任务完成，关闭浏览器")
                
            except asyncio.TimeoutError:
                logger.info(f'🔄 已过3分钟，刷新页面{open_url}...')
                tab.refresh()
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=200)
                except asyncio.TimeoutError:
                    logger.info("⏳ 页面已打开额外 200 秒，准备关闭浏览器")
            
            # 取消监控任务
            if monitor_task and not monitor_task.done():
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    logger.info("🛑 monitor_task 已取消")
                except Exception as e:
                    logger.warning(f"⚠️ monitor_task 取消时发生异常: {e}")

        else:
            logger.warning(f'❌ 没有找到[{keys}] 需要登录')
            
    except Exception as e:
        logger.error(f"浏览器任务发生异常: {e}", exc_info=True)
        
    finally:
        # 确保浏览器被关闭
        if browser:
            try:
                browser.quit()
                logger.info("✅ browser.quit() 执行成功")
            except Exception as e:
                logger.warning(f"browser.quit() 异常: {e}")
        
        # 强制清理所有残留的 Chromium 进程
        logger.info("🧹 强制清理残留的 chromium 进程...")
        os.system('pkill -f "/snap/chromium/.*chrome"')
        
        # 二次确认，使用更强制的方式
        time.sleep(1)
        os.system('pkill -9 -f "/snap/chromium/.*chrome" 2>/dev/null')
        logger.info("✅ 浏览器资源清理完成")


async def main():
    tasks = [check_url_loop(config) for config in URL_CONFIGS]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
