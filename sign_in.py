import requests
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ------------------ 配置 ------------------
EMAIL = "yephotoalbum@gmail.com"           # Navix 登录邮箱
PASSWORD = "69fYKuQJzM4LkuY"              # Navix 登录密码

# 邮件配置
EMAIL_SENDER = "你的邮箱@qq.com"           # 发件邮箱
EMAIL_PASSWORD = "邮箱授权码"              # SMTP 授权码
EMAIL_RECEIVER = "1916852351@qq.com"       # 收件邮箱
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465

# URL
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

try:
    resp = session.post(LOGIN_URL, json=login_payload)
    if resp.status_code == 200 and resp.json().get("success"):
        login_status = "登录成功"
    else:
        login_status = f"登录失败: {resp.text}"
        print(login_status)
        # 登录失败也继续记录日志和发邮件
except Exception as e:
    login_status = f"登录异常: {e}"
    print(login_status)

# ------------------ 获取签到页面 ------------------
try:
    sign_resp = session.get(SIGN_URL)
    soup = BeautifulSoup(sign_resp.text, "html.parser")
    btn = soup.find(id="btnSignIn")

    # 获取探花币和连续签到
    exp_elem = soup.find(id="expValue")
    days_elem = soup.find(id="consecutiveDays")

    exp = exp_elem.text.strip() if exp_elem else "未知"
    consecutive_days = days_elem.text.strip() if days_elem else "未知"

    # 判断是否签到
    if btn and btn.get("data-can-signin") == "true":
        # 这里签到是前端完成，发送 GET 访问即可触发
        sign_trigger = session.get(SIGN_URL)
        if sign_trigger.status_code == 200:
            status = "签到成功"
        else:
            status = "签到请求失败"
    else:
        status = "今天已签到"

except Exception as e:
    status = f"签到异常: {e}"
    exp = "未知"
    consecutive_days = "未知"

# ------------------ 构建日志 ------------------
log_text = f"{datetime.now()} - {login_status} - {status} - 连续签到天数: {consecutive_days}, 探花币: {exp}\n"
print(log_text)

# ------------------ 写入本地日志 ------------------
with open(LOG_FILE, "a", encoding="utf-8") as f:
    f.write(log_text)

# ------------------ 发送邮件 ------------------
try:
    msg = MIMEText(log_text, "plain", "utf-8")
    msg["From"] = Header("Navix签到机器人", "utf-8")
    msg["To"] = Header("收件人", "utf-8")
    msg["Subject"] = Header("每日签到日志", "utf-8")

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())

    print("日志邮件发送成功")
except Exception as e:
    print("日志邮件发送失败:", e)
