import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ------------------ 配置 ------------------
EMAIL = "yephotoalbum@gmail.com"
PASSWORD = "69fYKuQJzM4LkuY"

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

# ------------------ 获取探花币和连续签到 ------------------
exp_elem = soup.find(id="expValue")
days_elem = soup.find(id="consecutiveDays")

exp = exp_elem.text.strip() if exp_elem else "未知"
consecutive_days = days_elem.text.strip() if days_elem else "未知"

# ------------------ 判断是否签到 ------------------
if btn and btn.get("data-can-signin") == "true":
    sign_resp = session.get(SIGN_URL)
    if sign_resp.status_code == 200:
        status = "签到成功"
    else:
        status = "签到请求失败"
else:
    status = "今天已签到"

# ------------------ 输出 GitHub Actions 日志 ------------------
print(f"{datetime.now()} - {status}")
print(f"连续签到天数: {consecutive_days}, 探花币: {exp}")

# ------------------ 日志文件 ------------------
with open(LOG_FILE, "a", encoding="utf-8") as f:
    f.write(f"{datetime.now()} - {status} - 连续签到天数: {consecutive_days}, 探花币: {exp}\n")
