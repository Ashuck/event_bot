import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os


EMAIL_HOST = os.getenv("EMAIL_HOST", None)
EMAIL_USER = os.getenv("EMAIL_USER", None)
DEFAULT_TO_EMAIL = os.getenv("DEFAULT_TO_EMAIL", None)
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", None)


def send_mail(text, subject):
    server = EMAIL_HOST
    sender = EMAIL_USER

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = DEFAULT_TO_EMAIL
    msg['Reply-To'] = sender
    msg['Return-Path'] = sender
    msg['Bcc'] = sender

    part_html = MIMEText(text, 'plain',  'utf-8')
    msg.attach(part_html)

    mail = smtplib.SMTP_SSL(server)
    mail.login(EMAIL_USER, EMAIL_PASSWORD)
    mail.sendmail(sender, DEFAULT_TO_EMAIL, msg.as_string())
    mail.quit()