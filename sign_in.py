import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ------------------ 配置 ------------------
# 【修改点 1】: 将单个账号配置改为账号列表
# 请在你的环境变量中设置如下信息：
# NAVIX_EMAIL_1, NAVIX_PASSWORD_1
# NAVIX_EMAIL_2, NAVIX_PASSWORD_2
# ... 如果有更多账号，以此类推
ACCOUNTS = []
i = 1
while True:
    email = os.environ.get(f"NAVIX_EMAIL_{i}")
    password = os.environ.get(f"NAVIX_PASSWORD_{i}")
    if email and password:
        ACCOUNTS.append({"email": email, "password": password})
        i += 1
    else:
        # 如果找不到 NAVIX_EMAIL_i, 就停止添加
        break

LOGIN_URL = "https://navix.site/login"
SIGN_URL = "https://navix.site/sign_in"
LOG_FILE = "sign_log.txt"

# 邮件发送配置 (无需修改)
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")      # 发件人
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # 发件人授权码
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")  # 收件人

# ------------------ 邮件发送函数 ------------------
def send_email(subject, body):
    # 检查邮件配置是否存在
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
    # 创建北京时间时区 (UTC+8)
    beijing_tz = timezone(timedelta(hours=8))
    # 获取当前的北京时间并格式化
    beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    # 【修改点 2】: 创建一个列表来存储所有账号的日志
    all_logs = []

    if not ACCOUNTS:
        print("未找到任何账号配置，请检查环境变量。")
        log_entry = f"{beijing_time} - 错误：未配置任何账号信息。"
        all_logs.append(log_entry)
    
    # 【修改点 3】: 循环处理每个账号
    for account in ACCOUNTS:
        email = account["email"]
        password = account["password"]
        
        print(f"--- 开始处理账号: {email} ---")
        
        session = requests.Session()
        login_payload = {
            "email": email,
            "password": password,
            "rememberMe": False
        }
        
        login_status = ""
        status = ""
        exp = "未知"
        consecutive_days = "未知"

        # ------------------ 登录 ------------------
        try:
            resp = session.post(LOGIN_URL, json=login_payload)
            if resp.status_code == 200 and resp.json().get("success"):
                login_status = "登录成功"
            else:
                login_status = f"登录失败: {resp.text}"
                log_entry = f"账号 {email}: {login_status}"
                all_logs.append(log_entry)
                print(log_entry)
                continue # 处理下一个账号
        except Exception as e:
            login_status = f"登录异常: {e}"
            log_entry = f"账号 {email}: {login_status}"
            all_logs.append(log_entry)
            print(log_entry)
            continue # 处理下一个账号

        # ------------------ 获取签到页面并执行签到 ------------------
        try:
            sign_resp = session.get(SIGN_URL)
            sign_resp.raise_for_status() # 如果请求失败则抛出异常
            soup = BeautifulSoup(sign_resp.text, "html.parser")
            
            exp_elem = soup.find(id="expValue")
            days_elem = soup.find(id="consecutiveDays")
            exp = exp_elem.text.strip() if exp_elem else "未知"
            consecutive_days = days_elem.text.strip() if days_elem else "未知"
            
            btn = soup.find(id="btnSignIn")
            if btn and btn.get("data-can-signin") == "true":
                # 签到操作通常是点击按钮后发出的，这里模拟再次访问页面可能就是签到逻辑
                sign_action_resp = session.get(SIGN_URL) # 脚本原逻辑是再次GET
                if sign_action_resp.status_code == 200:
                    status = "签到成功"
                    # 重新获取签到后的信息
                    soup_after = BeautifulSoup(sign_action_resp.text, "html.parser")
                    exp_elem_after = soup_after.find(id="expValue")
                    days_elem_after = soup_after.find(id="consecutiveDays")
                    exp = exp_elem_after.text.strip() if exp_elem_after else exp
                    consecutive_days = days_elem_after.text.strip() if days_elem_after else consecutive_days
                else:
                    status = f"签到请求失败, 状态码: {sign_action_resp.status_code}"
            else:
                status = "今天已签到"

        except Exception as e:
            status = f"签到异常: {e}"
        
        # ------------------ 格式化当前账号的日志 ------------------
        log_entry = f"账号: {email} - {login_status} - {status} - 连续签到: {consecutive_days}, 币: {exp}"
        print(log_entry)
        all_logs.append(log_entry)

    # ------------------ 汇总并输出日志 ------------------
    # 【修改点 4】: 将所有日志汇总
    final_log_content = f"{beijing_time}\n" + "\n".join(all_logs)
    
    print("\n--- 任务总结 ---")
    print(final_log_content)
    print("----------------")

    # 写入日志文件
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(final_log_content + "\n\n")

    # ------------------ 发送邮件 ------------------
    send_email("每日签到日志 (多账号)", final_log_content)

if __name__ == "__main__":
    main()
