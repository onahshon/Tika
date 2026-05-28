import html
import logging
import traceback

import resend

from backend.app.core.config import settings
from backend.app.services.attorney_config import get_attorney_config

logger = logging.getLogger(__name__)

RLM = "\u200f"


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

    body = _build_text_body(contact_lines, transcript)
    html_body = _build_html_body(contact_lines, transcript)

    payload = {
        "from": settings.resend_from,
        "to": [config["email"]],
        "subject": f"פנייה חדשה מטיקה: {name}",
        "text": body,
        "html": html_body,
    }
    if email:
        payload["reply_to"] = email

    logger.info(
        "notify_attorney: sending from=%s to=%s attorney_id=%s",
        settings.resend_from,
        config["email"],
        attorney_id,
    )
    try:
        result = resend.Emails.send(payload)
        email_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", result)
        logger.info("notify_attorney: sent ok id=%s", email_id)
        return True
    except Exception:
        logger.error("notify_attorney Resend error:\n%s", traceback.format_exc())
        return False


def _build_text_body(contact_lines: list[str], transcript: str) -> str:
    sections = ["\n".join(_rtl_line(line) for line in contact_lines)]
    if transcript:
        sections.append(_rtl_line("תמלול השיחה") + "\n\n" + _format_transcript_text(transcript))

    return "\n\n".join(sections)


def _format_transcript_text(transcript: str) -> str:
    return "\n".join(_rtl_line(line) for line in transcript.splitlines())


def _rtl_line(line: str) -> str:
    return f"{RLM}{line}"


def _build_html_body(contact_lines: list[str], transcript: str) -> str:
    contact_html = "\n".join(_html_line(line) for line in contact_lines)
    transcript_html = ""
    if transcript:
        transcript_html = f"""
          <h2 style="font-size:16px;line-height:1.5;margin:24px 0 10px;color:#111827;">תמלול השיחה</h2>
          <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:16px;">
            {"".join(_html_line(line) for line in transcript.splitlines())}
          </div>
        """

    return f"""<!doctype html>
<html lang="he" dir="rtl">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
  </head>
  <body dir="rtl" style="margin:0;background:#ffffff;color:#111827;font-family:Arial,'Helvetica Neue',sans-serif;text-align:right;direction:rtl;">
    <main dir="rtl" style="max-width:680px;margin:0 auto;padding:24px;direction:rtl;text-align:right;">
      <h1 style="font-size:20px;line-height:1.4;margin:0 0 16px;color:#111827;">פנייה חדשה מטיקה</h1>
      <section dir="rtl" style="font-size:15px;line-height:1.7;margin:0;direction:rtl;text-align:right;">
        {contact_html}
        {transcript_html}
      </section>
    </main>
  </body>
</html>"""


def _html_line(line: str) -> str:
    return (
        '<div dir="rtl" style="direction:rtl;text-align:right;margin:0 0 6px;">'
        f"{html.escape(line)}"
        "</div>"
    )
