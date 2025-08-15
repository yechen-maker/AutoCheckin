import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ------------------ 配置 ------------------
EMAIL = "yephotoalbum@gmail.com"       # 你的邮箱
PASSWORD = "69fYKuQJzM4LkuY"           # 你的密码

LOGIN_URL = "https://navix.site/login"
SIGN_URL = "https://navix.site/sign_in"
LOG_FILE = "sign_log.txt"

# ------------------ 登录 ------------------
session = requests.Session()
login_payload = {
    "email": EMAIL,
    "password": PASSWORD,
    "rememberMe": False
}

resp = session.post(LOGIN_URL, json=login_payload)
if resp.status_code == 200 and resp.json().get("success"):
    print("登录成功")
else:
    print("登录失败:", resp.text)
    exit()

# ------------------ 获取签到页面 ------------------
sign_resp = session.get(SIGN_URL)
soup = BeautifulSoup(sign_resp.text, "html.parser")
btn = soup.find(id="btnSignIn")

# ------------------ 判断是否签到 ------------------
if btn and btn.get("data-can-signin") == "true":
    # GET /sign_in 本身就完成签到
    sign_resp = session.get(SIGN_URL)
    if sign_resp.status_code == 200:
        print("签到成功")
        status = "签到成功"
    else:
        print("签到请求失败")
        status = "签到请求失败"
else:
    print("今天已签到")
    status = "已签到"

# ------------------ 日志 ------------------
with open(LOG_FILE, "a", encoding="utf-8") as f:
    f.write(f"{datetime.now()} - {status}\n")
