import json
import logging
import urllib.error
import urllib.request

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

    contact_lines = [f"שם: {name}", f"טלפון: {phone}"]
    if email:
        contact_lines.append(f"אימייל: {email}")

    body = "\n".join(contact_lines) + "\n\n---\n\n" + transcript

    payload = {
        "from": settings.resend_from,
        "to": [config["email"]],
        "subject": f"Tika Law — ליד חדש: {name}",
        "text": body,
    }

    try:
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            return 200 <= res.status < 300
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        logger.error("Resend API error %s: %s", e.code, body_bytes.decode(errors="replace"))
        return False
    except Exception as e:
        logger.error("notify_attorney unexpected error: %s", e)
        return False
