import json
from typing import Any

from openai import OpenAI

from backend.app.core.config import settings
from backend.app.services.intake_engine import PhraseContext

EXTRACTION_PROMPT = """
You are extracting facts from a Hebrew employment-law intake conversation.
You will receive:
- The user's latest message
- The last question asked by the assistant
- The slot the assistant was trying to fill

CRITICAL: Interpret short answers in the CONTEXT of the question asked.
- If asked about employment status and user says "עובד" -> still_employed
- If asked about duration and user says "3 שנים" -> "3 שנים"
- Tolerate Hebrew typos, such as "קחבלתי" for "קיבלתי"
- Extract partial info. Do not require full sentences.

Fields:
- employer_name: string or null
- employment_duration: string or null
- procedural_stage: one of hearing_scheduled, hearing_completed, before_hearing, dismissal_stage, wage_issue, harassment_or_discrimination, unknown, or null
- current_status: one of still_employed, terminated, resigned, unpaid_leave, unknown, or null
- documentation_exists: one of yes, no, unclear, or null
- urgency: one of immediate, near_term, dated, not_urgent, unclear, or null
- signed_documents: one of signed, not_signed, requested, unclear, or null

Return only JSON.
"""

PHRASING_PROMPT = """
You are writing one short Hebrew message for an Israeli employment-law intake coordinator.
The backend already selected the next required step. Do not change the meaning.

Style:
- concise, professional, human
- usually under 12 Hebrew words
- no legal conclusions
- no promises
- no exaggerated empathy
- no repetitive "תודה, הבנתי"
- don't start every message with "תודה, הבנתי" — vary acknowledgments or skip them when not needed
- ask only the selected question

Special canonical messages:
- If canonical_message is "retry_unclear_answer", politely ask the user to clarify. Example: "לא הצלחתי להבין, אפשר לפרט קצת יותר?"
- If canonical_message is "fallback_after_retries", ask for phone number so the attorney can call back. Example: "אשמח אם תשאיר/י מספר טלפון ועורכת הדין תחזור אליך"

Return only JSON: {"assistant_message": "..."}
"""


def extract_with_openai(
    message: str,
    last_asked_slot: str | None = None,
    last_question: str | None = None,
) -> dict[str, str]:
    if not settings.openai_api_key:
        return {}

    user_payload = {
        "user_message": message,
        "last_asked_slot": last_asked_slot,
        "last_question": last_question,
    }

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        payload = json.loads(response.choices[0].message.content or "{}")
    except Exception:
        return {}

    return _map_extraction(payload)


def phrase_with_openai(context: PhraseContext) -> str | None:
    if not settings.openai_api_key:
        return None

    payload = {
        "selected_slot": context.next_slot,
        "canonical_message": context.canonical_message,
        "classification": context.classification,
        "score": context.score,
        "known_slots": context.slots,
        "latest_user_message": context.latest_user_message,
        "turn_count": context.turn_count,
    }

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": PHRASING_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0.35,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        message = str(data.get("assistant_message", "")).strip()
    except Exception:
        return None

    if not message or len(message) > 220:
        return None

    return message


def _map_extraction(payload: dict[str, Any]) -> dict[str, str]:
    slots: dict[str, str] = {}

    if _clean(payload.get("employer_name")):
        slots["employer"] = _clean(payload.get("employer_name"))
    if _clean(payload.get("employment_duration")):
        slots["employment_duration"] = _clean(payload.get("employment_duration"))
    if _clean(payload.get("procedural_stage")) and payload.get("procedural_stage") != "unknown":
        slots["procedural_stage"] = _clean(payload.get("procedural_stage"))
    if _clean(payload.get("current_status")) and payload.get("current_status") != "unknown":
        slots["employment_status"] = _clean(payload.get("current_status"))
    if payload.get("documentation_exists") in {"yes", "no"}:
        slots["documentation"] = "has_documents" if payload["documentation_exists"] == "yes" else "no_documents"
    if _clean(payload.get("urgency")) and payload.get("urgency") not in {"unclear", "not_urgent"}:
        slots["urgency"] = _clean(payload.get("urgency"))
    if payload.get("signed_documents") in {"signed", "not_signed", "requested"}:
        slots["signed_docs"] = _clean(payload.get("signed_documents"))

    return slots


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
