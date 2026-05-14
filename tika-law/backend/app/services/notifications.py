import json
import urllib.request

from backend.app.core.config import settings
from backend.app.services.attorney_config import get_attorney_config


def notify_attorney(
    attorney_id: str,
    name: str,
    phone: str,
    email: str | None,
    transcript: str,
) -> bool:
    if not settings.resend_api_key:
        return False

    config = get_attorney_config(attorney_id)
    if not config or not config.get("email"):
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
    except Exception:
        return False
