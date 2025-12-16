import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)


def send_email(subject, message, user_id, from_addr, to_addr, pwd):
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["to"] = to_addr
    msg["Subject"] = subject  # 标题

    msg.attach(MIMEText(message, "html"))  # 正文

    try:
        with smtplib.SMTP("mail01-ap-dg.dg.apitech.com.tw", 465) as server:
            server.starttls()
            server.login(f"APINTDMN3\\{user_id}", pwd)
            server.send_message(msg)
            logger.info("邮件发送成功！")
            return True
    except Exception as e:
        logger.error(f"邮件发送失败:{e}")
        return False


if __name__ == "__main__":
    sub = "1"
    message = "<html><p>It's test.</p></html>"
    userid = "22400616"
    from_ad = "Lucas_Li@acbel.com"
    to_ad = "Lucas_Li@acbel.com"
    pwd = "kS0708E"
    send_email(sub, message, userid, from_ad, to_ad, pwd)
