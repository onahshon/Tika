import smtplib
from email.message import EmailMessage

from backend.app.core.config import settings


def notify_attorney(subject: str, body: str) -> bool:
    if not all(
        [
            settings.attorney_notification_to,
            settings.attorney_notification_from,
            settings.smtp_host,
            settings.smtp_username,
            settings.smtp_password,
        ]
    ):
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.attorney_notification_from or ""
    message["To"] = settings.attorney_notification_to or ""
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except Exception:
        return False

    return True
