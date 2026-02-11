"""
Email Service - Send notification emails
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment
LAWYER_EMAIL = os.getenv("LAWYER_EMAIL", "drorlaib@gmail.com")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def send_notification_email(
    seller_name: str,
    property_address: str,
    drive_folder_link: str,
    smtp_server: str = None,
    smtp_port: int = None,
    smtp_user: str = None,
    smtp_password: str = None
) -> dict:
    """
    Send notification email to lawyer about new transaction.

    Note: For Gmail, you need to use App Password (not regular password)
    https://myaccount.google.com/apppasswords
    """

    subject = f"עסקת נדל\"ן חדשה - {property_address}"

    body = f"""
שלום,

התקבלה עסקת נדל״ן חדשה במערכת.

פרטי העסקה:
- מוכר: {seller_name}
- נכס: {property_address}

קישור לתיקייה ב-Google Drive:
{drive_folder_link}

המערכת האוטומטית
"""

    # Use environment variables if parameters not provided
    smtp_server = smtp_server or SMTP_SERVER
    smtp_port = smtp_port or SMTP_PORT
    smtp_user = smtp_user or SMTP_USER
    smtp_password = smtp_password or SMTP_PASSWORD

    # If SMTP not configured, just return the info
    if not smtp_user or not smtp_password:
        return {
            "success": True,
            "message": "Email notification ready (SMTP not configured)",
            "to": LAWYER_EMAIL,
            "subject": subject,
            "body": body,
            "drive_link": drive_folder_link
        }

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = LAWYER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return {"success": True, "message": "Email sent successfully"}

    except Exception as e:
        return {"success": False, "message": str(e)}
