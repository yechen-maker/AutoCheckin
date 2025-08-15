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
LOGIN_URL = "https://navix.site/login"
SIGN_URL = "https://navix.site/sign_in"
LOG_FILE = "sign_log.txt"

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")      # 发件人
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # 发件人授权码
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")  # 收件人

# ------------------ 邮件发送函数 ------------------
def send_email(subject, body):
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = Header(EMAIL_SENDER, 'utf-8')
    msg['To'] = Header(EMAIL_RECEIVER, 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    # --- 开始调试代码 ---
    # 打印将要用于登录的用户名，检查它是否正确
    print(f"DEBUG: Attempting to log in with username: '{EMAIL_SENDER}'")
    
    # 打印密码的长度和前4位，用于核对
    if EMAIL_PASSWORD:
        print(f"DEBUG: Password length is: {len(EMAIL_PASSWORD)}")
        print(f"DEBUG: First 4 characters of password are: '{EMAIL_PASSWORD[:4]}'")
    else:
        print("DEBUG: EMAIL_PASSWORD secret is empty or not found!")
    # --- 结束调试代码 ---

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        print("日志邮件发送成功")
    except Exception as e:
        print("日志邮件发送失败:", e)

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
        send_email("探花TV 每日签到日志", login_status)
        exit()
except Exception as e:
    login_status = f"登录异常: {e}"
    print(login_status)
    send_email("探花TV 每日签到日志", login_status)
    exit()

# ------------------ 获取签到页面 ------------------
try:
    sign_resp = session.get(SIGN_URL)
    soup = BeautifulSoup(sign_resp.text, "html.parser")
    btn = soup.find(id="btnSignIn")

    exp_elem = soup.find(id="expValue")
    days_elem = soup.find(id="consecutiveDays")
    exp = exp_elem.text.strip() if exp_elem else "未知"
    consecutive_days = days_elem.text.strip() if days_elem else "未知"

    # ------------------ 执行签到 ------------------
    if btn and btn.get("data-can-signin") == "true":
        sign_resp = session.get(SIGN_URL)
        if sign_resp.status_code == 200:
            status = "签到成功"
        else:
            status = "签到请求失败"
    else:
        status = "今天已签到"

except Exception as e:
    status = f"签到异常: {e}"
    exp = "未知"
    consecutive_days = "未知"

# ------------------ 输出日志 ------------------
log_text = f"{datetime.now()} - {login_status} - {status} - 连续签到天数: {consecutive_days}, 探花币: {exp}"
print(log_text)

# 写入日志文件
with open(LOG_FILE, "a", encoding="utf-8") as f:
    f.write(log_text + "\n")

# ------------------ 发送邮件 ------------------
send_email("探花TV 每日签到日志", log_text)
