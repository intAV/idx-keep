# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import math
import pyautogui
import pyscreenshot as ImageGrab
from PIL import ImageDraw
from DrissionPage import Chromium, ChromiumOptions
import schedule
import logging


# ------------------ 日志配置 ------------------

class BeijingFormatter(logging.Formatter):
    converter = time.localtime  # 默认使用本地时间

    def formatTime(self, record, datefmt=None):
        # 将时间转换为北京时间（UTC+8）
        beijing_time = time.gmtime(record.created + 8 * 3600)
        return time.strftime(datefmt, beijing_time)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('./lunes.log')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

formatter = BeijingFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='[%Y-%m-%d %H:%M:%S]')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ------------------ 人类化点击 ------------------

def human_like_click(x, y, click_duration=0.1, movement_intensity=25, total_move_duration=0.918):
    current_x, current_y = pyautogui.position()
    movement_type = random.choice(['direct', 'curved', 'zigzag'])

    if movement_type == 'direct':
        move_time = total_move_duration * 0.7
        pyautogui.moveTo(x, y, duration=move_time)
        adjust_time = total_move_duration * 0.3
        pyautogui.moveRel(random.randint(-5, 5), random.randint(-5, 5), duration=adjust_time)

    elif movement_type == 'curved':
        generate_random_movement_trajectory(current_x, current_y, x, y, intensity=movement_intensity, total_duration=total_move_duration)

    elif movement_type == 'zigzag':
        perform_zigzag_movement(current_x, current_y, x, y, total_duration=total_move_duration)

    time.sleep(random.uniform(0.05, 0.15))
    pyautogui.click(duration=click_duration)
    time.sleep(random.uniform(0.1, 0.2))

def generate_random_movement_trajectory(start_x, start_y, end_x, end_y, intensity=50, total_duration=1.0):
    dx = end_x - start_x
    dy = end_y - start_y
    distance = math.sqrt(dx**2 + dy**2)
    if distance < 10:
        pyautogui.moveTo(end_x, end_y, duration=total_duration)
        return

    base_steps = max(8, min(20, int(distance / 20)))
    steps = random.randint(base_steps - 2, base_steps + 2)
    points = []

    for i in range(1, steps):
        progress = i / steps
        linear_x = start_x + dx * progress
        linear_y = start_y + dy * progress
        offset_x = random.randint(-intensity, intensity)
        offset_y = random.randint(-intensity, intensity)
        factor = 1 - progress * 0.8
        final_x = linear_x + offset_x * factor
        final_y = linear_y + offset_y * factor
        points.append((final_x, final_y))

    points.append((end_x, end_y))
    base_time = total_duration / len(points)

    for i, (px, py) in enumerate(points):
        duration = base_time * random.uniform(0.7, 1.3)
        pyautogui.moveTo(px, py, duration=duration)
        if i < len(points) - 1:
            time.sleep(random.uniform(0.01, 0.03))

def perform_zigzag_movement(start_x, start_y, end_x, end_y, total_duration=1.0):
    mid_x = (start_x + end_x) / 2
    mid_y = (start_y + end_y) / 2
    offset1 = random.randint(20, 50) * random.choice([-1, 1])
    offset2 = random.randint(15, 40) * random.choice([-1, 1])
    points = [(start_x, start_y),
              (mid_x + offset1, mid_y + offset1),
              (mid_x - offset2, mid_y - offset2),
              (end_x, end_y)]
    base_time = total_duration / len(points)

    for i, (px, py) in enumerate(points):
        duration = base_time * random.uniform(0.8, 1.2)
        pyautogui.moveTo(px, py, duration=duration)
        if i < len(points) - 1:
            time.sleep(random.uniform(0.02, 0.05))

# ------------------ 浏览器与自动化 ------------------

def init_browser():
    co = ChromiumOptions()
    co.set_paths(browser_path='/usr/bin/chromium-browser')
    co.set_user_data_path('./Default')
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0')
    co.set_argument('--window-position=0,0')
    co.set_argument('--window-size=800,800')
    return Chromium(co)

def login_and_capture(tab):
    try:
        logger.info("🚀 开始自动登录流程")
        time.sleep(13)
        ImageGrab.grab().save("./pic/browser_screenshot.png")
        logger.info("📸 截图browser_screenshot.png完成,开始定位按钮")

        location = pyautogui.locate("./pic/button_image.png", "./pic/browser_screenshot.png")
        if location is None:
            raise ValueError("未找到匹配图像")

        center = pyautogui.center(location)
        logger.info(f"✅ 找到坐标：x={center.x}, y={center.y}")
        human_like_click(center.x, center.y)
        time.sleep(5)
        ImageGrab.grab().save("./pic/1.png")
        logger.info("📸 1.png截图完成")

        tab.ele('xpath://*[@id="email"]').input('用户名')
        tab.ele('xpath://*[@id="password"]').input('密码')
        tab.ele('xpath://button[@class="hover:scale-105 w-full bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition duration-200"]').click()
        logger.info("✅ 已点击登录按钮")

        time.sleep(8)
        ImageGrab.grab().save("./pic/2.png")
        location = pyautogui.locate("./pic/save.png", "./pic/2.png")
        if location is None:
            raise ValueError("未找到匹配图像")

        center = pyautogui.center(location)
        human_like_click(center.x, center.y)
        time.sleep(2)
        ImageGrab.grab().save("./pic/3.png")
        logger.info("✅ 3.png截图完成")

        ele = tab.ele('@text():my-server')
        if ele:
            logger.info("✅ 找到元素[my-server],开始点击")
            ele.click()
            time.sleep(5)
            ImageGrab.grab().save("./pic/4.png")
            logger.info("📸 4.png截图完成")
        else:
            logger.info("❌ 页面中未找到包含 [my-server] 的元素")

    except Exception as e:
        logger.error(f"❌ 操作过程中出现错误: {e}")

# ------------------ 主入口 ------------------

def main():
    logger.info("🚀 00:00时间到,登录账号")
    browser = init_browser()
    try:
        tab = browser.new_tab()
        tab.get("https://betadash.lunes.host/")
        tab.wait.doc_loaded()
        logger.info("✅ 页面已加载完成")

        ele = tab.ele('@text():my-server')
        if ele:
            logger.info("✅ 找到元素[my-server],开始点击")
            ele.click()
            time.sleep(5)
            ImageGrab.grab().save("./pic/4.png")
            logger.info("📸 4.png截图完成")
        else:
            logger.info("❌ 页面中未找到包含 [my-server] 的元素")
            login_and_capture(tab)

    except Exception as e:
        logger.error(f"❌ 主流程发生异常: {e}")

    finally:
        browser.quit()
        logger.info("✅ 浏览器已关闭")




# ------------------ 定时任务调度 ------------------

schedule.every().day.at("16:00").do(main)

logger.info("🕒 定时任务已启动,将在北京时间每天00:00执行")

while True:
    schedule.run_pending()
    time.sleep(20)
