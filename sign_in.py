import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ------------------ 配置 ------------------
ACCOUNTS = []

# 1. 检查无数字后缀的基础账号
base_email = os.environ.get("NAVIX_EMAIL")
base_password = os.environ.get("NAVIX_PASSWORD")
if base_email and base_password:
    ACCOUNTS.append({"email": base_email, "password": base_password})

# 2. 从 2 开始检查带数字后缀的账号
i = 2
while True:
    email = os.environ.get(f"NAVIX_EMAIL{i}")
    password = os.environ.get(f"NAVIX_PASSWORD{i}")
    if email and password:
        ACCOUNTS.append({"email": email, "password": password})
        i += 1
    else:
        break

LOGIN_URL = "https://navix.site/login"
SIGN_URL = "https://navix.site/sign_in"
SIGN_API = "https://navix.site/api/sign-in"
LOG_FILE = "sign_log.txt"

# 邮件发送配置
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")


# ------------------ 邮件发送函数 ------------------
def send_email(subject, body):
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
        print("邮件配置不完整，跳过发送邮件。")
        return

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = Header(EMAIL_SENDER, 'utf-8')
    msg['To'] = Header(EMAIL_RECEIVER, 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        print("日志邮件发送成功")
    except Exception as e:
        print(f"日志邮件发送失败: {e}")


# ------------------ 主执行逻辑 ------------------
def main():
    beijing_tz = timezone(timedelta(hours=8))
    beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

    all_logs = []

    if not ACCOUNTS:
        print("未找到任何账号配置，请检查仓库的 Secrets 设置。")
        log_entry = f"{beijing_time} - 错误：未配置任何账号信息。"
        all_logs.append(log_entry)

    for account in ACCOUNTS:
        email = account["email"]
        password = account["password"]

        print(f"--- 开始处理账号: {email} ---")

        session = requests.Session()
        login_payload = {"email": email, "password": password, "rememberMe": False}

        login_status = ""
        status = ""
        exp = "未知"
        consecutive_days = "未知"

        # 登录
        try:
            resp = session.post(LOGIN_URL, json=login_payload)
            if resp.status_code == 200 and resp.json().get("success"):
                login_status = "登录成功"
            else:
                login_status = f"登录失败: {resp.text}"
                log_entry = f"账号 {email}: {login_status}"
                all_logs.append(log_entry)
                print(log_entry)
                continue
        except Exception as e:
            login_status = f"登录异常: {e}"
            log_entry = f"账号 {email}: {login_status}"
            all_logs.append(log_entry)
            print(log_entry)
            continue

        # 获取签到页面，提取 token
        try:
            sign_page_resp = session.get(SIGN_URL)
            sign_page_resp.raise_for_status()
            soup = BeautifulSoup(sign_page_resp.text, "html.parser")

            exp_elem = soup.find(id="expValue")
            days_elem = soup.find(id="consecutiveDays")
            exp = exp_elem.text.strip() if exp_elem else "未知"
            consecutive_days = days_elem.text.strip() if days_elem else "未知"

            btn = soup.find(id="btnSignIn")
            if btn and btn.get("data-can-signin") == "true":
                # 可能有 csrf token
                csrf_token_elem = soup.find("meta", {"name": "csrf-token"})
                csrf_token = csrf_token_elem["content"] if csrf_token_elem else None

                headers = {
                    "Referer": SIGN_URL,
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                }
                if csrf_token:
                    headers["X-CSRF-Token"] = csrf_token

                sign_action_resp = session.post(SIGN_API, headers=headers)
                if sign_action_resp.status_code == 200:
                    status = "签到成功"
                    # 刷新数据
                    soup_after = BeautifulSoup(session.get(SIGN_URL).text, "html.parser")
                    exp_elem_after = soup_after.find(id="expValue")
                    days_elem_after = soup_after.find(id="consecutiveDays")
                    exp = exp_elem_after.text.strip() if exp_elem_after else exp
                    consecutive_days = days_elem_after.text.strip() if days_elem_after else consecutive_days
                else:
                    status = f"签到失败, 状态码: {sign_action_resp.status_code}"
            else:
                status = "今天已签到"

        except Exception as e:
            status = f"签到异常: {e}"

        log_entry = f"账号: {email} - {login_status} - {status} - 连续签到: {consecutive_days}, 币: {exp}"
        print(log_entry)
        all_logs.append(log_entry)

    final_log_content = f"{beijing_time}\n" + "\n".join(all_logs)

    print("\n--- 任务总结 ---")
    print(final_log_content)
    print("----------------")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(final_log_content + "\n\n")

    send_email("每日签到日志 (多账号)", final_log_content)


if __name__ == "__main__":
    main()
