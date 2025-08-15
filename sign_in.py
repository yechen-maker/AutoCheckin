import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import logging

# ------------------ 日志配置 ------------------
# 配置日志记录，使其同时输出到控制台和文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sign_log.txt", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ------------------ 配置 ------------------
# 从环境变量获取配置信息
EMAIL = os.environ.get("NAVIX_EMAIL")
PASSWORD = os.environ.get("NAVIX_PASSWORD")
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")      # 发件人
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # 发件人授权码
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")  # 收件人

# 网站URL
BASE_URL = "https://navix.site"
LOGIN_URL = f"{BASE_URL}/login"
USER_PAGE_URL = f"{BASE_URL}/user" # 用户页面，用于检查登录状态和获取信息
SIGN_URL = f"{BASE_URL}/sign_in" # 签到页面/操作URL

# ------------------ 邮件发送函数 ------------------
def send_email(subject, body):
    """发送邮件通知"""
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
        logging.warning("邮件发送配置不完整，跳过发送。")
        return

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = Header(f"签到脚本 <{EMAIL_SENDER}>", 'utf-8')
    msg['To'] = Header(f"管理员 <{EMAIL_RECEIVER}>", 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    try:
        # 增加了 timeout=10 参数，以应对网络延迟，提高在GitHub Actions上的稳定性
        with smtplib.SMTP_SSL('smtp.qq.com', 465, timeout=10) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        logging.info("日志邮件发送成功")
    except Exception as e:
        logging.error(f"日志邮件发送失败: {e}")

# ------------------ 主函数 ------------------
def main():
    """主执行函数"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": BASE_URL
    })
    
    log_messages = []

    # 1. 登录
    try:
        login_payload = {
            "email": EMAIL,
            "password": PASSWORD,
            "rememberMe": "true"
        }
        resp = session.post(LOGIN_URL, json=login_payload)
        resp.raise_for_status() # 如果状态码不是2xx，则抛出异常
        
        if resp.json().get("success"):
            logging.info("登录成功")
            log_messages.append("登录成功")
        else:
            error_msg = f"登录失败: {resp.text}"
            logging.error(error_msg)
            log_messages.append(error_msg)
            send_email("探花TV 签到失败", "\n".join(log_messages))
            return
    except Exception as e:
        error_msg = f"登录请求异常: {e}"
        logging.error(error_msg)
        log_messages.append(error_msg)
        send_email("探花TV 签到失败", "\n".join(log_messages))
        return

    # 2. 签到
    try:
        # 首先访问签到页面，检查是否已签到
        user_page_resp = session.get(SIGN_URL)
        user_page_resp.raise_for_status()
        
        soup = BeautifulSoup(user_page_resp.text, "html.parser")
        
        # 根据你最初的逻辑，查找按钮和 'data-can-signin' 属性
        btn = soup.find(id="btnSignIn")
        
        if btn and btn.get("data-can-signin") == "true":
            logging.info("检测到今天尚未签到，开始执行签到...")
            
            # 按照你的要求，使用GET请求进行签到
            sign_resp = session.get(SIGN_URL) 
            sign_resp.raise_for_status()
            
            # 简单的GET请求可能不会返回JSON，我们通过状态码判断
            if sign_resp.status_code == 200:
                status = "签到成功"
                logging.info(status)
            else:
                status = f"签到请求失败，状态码: {sign_resp.status_code}"
                logging.warning(status)
        else:
            status = "今天已经签到过了"
            logging.info(status)
        
        log_messages.append(status)

        # 重新获取用户信息以更新数据
        final_page_resp = session.get(SIGN_URL)
        soup = BeautifulSoup(final_page_resp.text, "html.parser")
        exp_elem = soup.find(id="expValue")
        days_elem = soup.find(id="consecutiveDays")
        
        exp = exp_elem.text.strip() if exp_elem else "未知"
        consecutive_days = days_elem.text.strip() if days_elem else "未知"
        
        log_messages.append(f"连续签到天数: {consecutive_days}")
        log_messages.append(f"探花币: {exp}")

    except Exception as e:
        error_msg = f"签到或获取信息时发生异常: {e}"
        logging.error(error_msg)
        log_messages.append(error_msg)

    # 3. 发送最终日志邮件
    final_log = "\n".join(log_messages)
    send_email("探花TV 每日签到日志", final_log)

if __name__ == "__main__":
    main()
