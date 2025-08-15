import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ------------------ 配置 ------------------
EMAIL = os.environ.get("NAVIX_EMAIL")
PASSWORD = os.environ.get("NAVIX_PASSWORD")
SIGN_URL = "https://navix.site/sign_in"
LOGIN_URL = "https://navix.site/login"
LOG_FILE = "sign_log.txt"

# 邮件配置
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465

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

# ------------------ 输出日志 ------------------
log_text = f"{datetime.now()} - {status} - 连续签到天数: {consecutive_days}, 探花币: {exp}"
print(log_text)

with open(LOG_FILE, "a", encoding="utf-8") as f:
    f.write(log_text + "\n")

# ------------------ 发送邮件通知 ------------------
try:
    msg = MIMEText(log_text, "plain", "utf-8")
    msg["From"] = Header("自动签到", "utf-8")
    msg["To"] = Header("自己", "utf-8")
    msg["Subject"] = Header("Navix 每日签到结果", "utf-8")

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_SENDER, EMAIL_PASS)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    print("邮件发送成功")
except Exception as e:
    print("邮件发送失败:", e)
