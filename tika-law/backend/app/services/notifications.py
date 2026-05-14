import logging

import resend

from backend.app.core.config import settings
from backend.app.services.attorney_config import get_attorney_config

logger = logging.getLogger(__name__)


def notify_attorney(
    attorney_id: str,
    name: str,
    phone: str,
    email: str | None,
    transcript: str,
) -> bool:
    if not settings.resend_api_key:
        logger.error("notify_attorney: RESEND_API_KEY not set")
        return False

    config = get_attorney_config(attorney_id)
    if not config or not config.get("email"):
        logger.error("notify_attorney: no config or email for attorney_id=%r", attorney_id)
        return False

    resend.api_key = settings.resend_api_key

    contact_lines = [f"שם: {name}", f"טלפון: {phone}"]
    if email:
        contact_lines.append(f"אימייל: {email}")

    body = "\n".join(contact_lines) + ("\n\n---\n\n" + transcript if transcript else "")

    try:
        resend.Emails.send({
            "from": settings.resend_from,
            "to": [config["email"]],
            "subject": f"Tika Law — ליד חדש: {name}",
            "text": body,
        })
        return True
    except Exception as e:
        logger.error("notify_attorney Resend error: %s", e)
        return False
