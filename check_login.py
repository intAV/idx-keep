import time
from DrissionPage import Chromium, ChromiumOptions

co = ChromiumOptions().headless()
co.set_paths(browser_path='/var/lib/snapd/snap/bin/chromium')
co.set_user_data_path('./Default')
co.set_proxy('http://192.168.200.14:10888')
co.set_argument('--no-sandbox')
co.set_argument('--disable-dev-shm-usage')
co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36')


browser = Chromium(co)

def test(url, keys):
    tab = browser.new_tab()
    tab.get(url)

    ele = tab.ele(f'xpath://*[contains(text(), "{keys}")]', timeout=30)
    if keys in tab.html:
        print(f'✅ 在 {url} 找到[{keys}]')
    else:
        print(f'❌ 在 {url} 没有找到[{keys}]')

# 检查cookie是否过期
# 执行多个测试，每个都在新标签页中打开
test('https://idx.google.com/', 'xray-keep')
test('https://idx.google.com/', 'flask-keep')
test('https://idx.google.com/', 'console')
time.sleep(1)
browser.quit()
