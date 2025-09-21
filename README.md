# idx-keep
一些非常炫酷的技术
### **🔴 注意**: 如果被谷歌官方检测到使用chromium浏览器加载账号被封与本人无关，至少我测试了很久是没有被封，没什么大不了一直在使用
### 1.使用snap安装chromium(版本一致)
### 2.本地登录，上传文件Default

<img width="836" height="584" alt="image" src="https://github.com/user-attachments/assets/5bf77f3d-9bad-4718-aef8-19900341b4a4" />
<img width="922" height="619" alt="image" src="https://github.com/user-attachments/assets/2d34cf9e-3c74-4edc-9266-ee5ad6280854" />

# lunes-keep
使用chromium浏览器绕过cloudflare-turnstile验证码
### 1.启动虚拟显示屏幕
```markdown
Xvfb :99 -screen 0 1024x768x24 &
```
### 2.使用图像匹配找到按钮，需要手动在browser_screenshot.png截取验证码按钮并保存为button_image.png
```python
pyautogui.locate("./pic/button_image.png", "./pic/browser_screenshot.png")
```
### 3.🔴服务器上面点选验证码返回ERROR,安装桌面环境(成功绕过的关键)
### 4.登录成功查找关键字元素[my-server],需自己修改
### 5.用户名和密码143 144行

<img width="759" height="598" alt="image" src="https://github.com/user-attachments/assets/30ecea70-fe97-412c-aa0e-15c3d091cadc" />
<img width="804" height="752" alt="image" src="https://github.com/user-attachments/assets/765ebe76-3349-4bc0-ad45-48b585dea075" />
<img width="811" height="773" alt="image" src="https://github.com/user-attachments/assets/15441d98-05f8-4331-a033-5998643ea5b7" />
<img width="804" height="695" alt="image" src="https://github.com/user-attachments/assets/803782e9-9ed7-4209-950e-1810917e7d05" />
