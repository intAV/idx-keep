# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import math
import pyautogui
import pyscreenshot as ImageGrab
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

# ------------------ 浏览器初始化 ------------------

def init_browser():
    co = ChromiumOptions()
    co.set_paths(browser_path='/usr/bin/chromium-browser')
    co.set_user_data_path('./Default')
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0')
    co.set_argument('--window-size=800,800')
    return Chromium(co)

# ------------------ 工具函数 ------------------

def capture_and_save(filename):
    ImageGrab.grab().save(f"./pic/{filename}")
    logger.info(f"📸 {filename} 截图完成")

def submit_login(tab, email, password):
    email_ele = tab.ele('xpath://*[@id="email"]')
    password_ele = tab.ele('xpath://*[@id="password"]')

    # 判断输入框是否已有值
    email_val = email_ele.attr('value')
    password_val = password_ele.attr('value')

    if not email_val:
        email_ele.input(email)

    if not password_val:
        password_ele.input(password)

    # 点击登录按钮
    tab.ele('xpath://button[@class="hover:scale-105 w-full bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition duration-200"]').click()
    logger.info("✅ 已点击登录按钮")

def save_password(image_name):
    location = pyautogui.locate("./pic/save.png", f"./pic/{image_name}")
    if location:
        center = pyautogui.center(location)
        human_like_click(center.x, center.y)
        logger.info("✅ 已点击记住用户名和密码")

def is_login(tab):
    keys = '@text():my-server'
    ele = tab.ele(keys, timeout=10)
    if ele:
        ele.click()
        tab.wait.doc_loaded()
        time.sleep(4)
        logger.info(f"✅ 找到元素 [{keys}] 点击成功")
        capture_and_save("ok.png")
        return True
    else:
        logger.warning(f"⚠️ 等待10秒钟后,没有找到元素 [{keys}]")
        return False

# ------------------ 登录主函数 ------------------

def login_and_capture(tab):
    try:
        logger.info("🚀 开始自动登录流程")
        time.sleep(4)
        capture_and_save("browser_screenshot.png")

        location = pyautogui.locate("./pic/button_image.png", "./pic/browser_screenshot.png")
        if location:
            center = pyautogui.center(location)
            logger.info(f"✅ 找到验证码坐标：x={center.x}, y={center.y}")
            human_like_click(center.x, center.y)
            time.sleep(9)
        
        capture_and_save("yzm.png")

        # 开始登录
        submit_login(tab, 用户名, 密码)
        time.sleep(8)
        capture_and_save("index.png")

        # 浏览器记住密码
        # save_password("index.png")

        # 打开指定页面
        return is_login(tab)

    except Exception as e:
        logger.error(f"❌ 登录过程中出现错误: {e}")
        return False

# ------------------ 主入口 ------------------

def main():
    logger.info("🚀 00:00时间到,登录账号")
    browser = init_browser()
    try:
        tab = browser.new_tab()
        tab.get("https://betadash.lunes.host/")
        tab.wait.doc_loaded()
        logger.info("✅ 页面已加载完成")

        # 最多尝试登录 3 次
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            if is_login(tab):
                break
            if login_and_capture(tab):
                break
            logger.warning("⚠️ 登录尝试失败，准备下一次尝试")

    except Exception as e:
        logger.error(f"❌ 主流程发生异常: {e}")

    finally:
        browser.quit()
        logger.info("✅ 浏览器已关闭")

# ------------------ 定时任务调度 ------------------
# main()
schedule.every().day.at("16:00").do(main)

logger.info("🕒 定时任务已启动,将在北京时间每天00:00执行")

while True:
    schedule.run_pending()
    time.sleep(20)

