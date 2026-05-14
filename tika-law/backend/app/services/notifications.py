import json
import urllib.request

from backend.app.services.attorney_config import get_attorney_config


def notify_attorney(
    attorney_id: str,
    name: str,
    phone: str,
    email: str | None,
    transcript: str,
) -> bool:
    config = get_attorney_config(attorney_id)
    if not config or not config.get("formspree_url"):
        return False

    payload: dict = {
        "שם": name,
        "טלפון": phone,
        "שיחה": transcript,
    }
    if email:
        payload["אימייל"] = email

    try:
        req = urllib.request.Request(
            config["formspree_url"],
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            body = json.loads(res.read())
            return body.get("ok", False)
    except Exception:
        return False
