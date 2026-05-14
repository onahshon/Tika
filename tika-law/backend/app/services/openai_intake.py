import json
from typing import Any

from openai import OpenAI

from backend.app.core.config import settings
from backend.app.services.intake_engine import IntakeState, PhraseContext

EXTRACTION_PROMPT = """
You are extracting facts from a Hebrew employment-law intake conversation.
You will receive the user's latest message, the recent conversation history,
the last question asked, and the slot being filled.

CRITICAL: Interpret short answers in the CONTEXT of the question asked and
the conversation history. "כן"/"לא" mean yes/no relative to what was asked.
Tolerate Hebrew typos (e.g. "קחבלתי" → "קיבלתי"). Extract partial info.

Fields to extract:
- employer_name: string or null
- employment_duration: string or null
- procedural_stage: one of hearing_scheduled, hearing_completed, before_hearing,
  dismissal_stage, wage_issue, harassment_or_discrimination, unknown, or null
- current_status: one of still_employed, terminated, resigned, unpaid_leave, unknown, or null
- documentation_exists: one of yes, no, unclear, or null
- urgency: one of immediate, near_term, dated, not_urgent, unclear, or null
- signed_documents: one of signed, not_signed, requested, unclear, or null

Return only JSON.
"""

CASE_ASSESSMENT_PROMPT = """
You are an intake coordinator at an Israeli employment-law firm.
A potential client just asked whether they have a case.

Based on the known facts and conversation history, give a brief honest preliminary assessment in Hebrew.

Guidelines:
- Very short tenure (days or 1-2 weeks): in Israel this is the probationary period — fewer protections, weaker case. Say so honestly but gently.
- Hearing scheduled: an active situation — worth consulting, but outcome depends on details
- Already terminated: check whether process was fair
- If little is known: say you need a bit more info before assessing
- Never promise outcomes or give legal guarantees
- Be honest, concise — 2-3 short sentences maximum
- End by asking for their phone number so the attorney can evaluate properly
- Professional but human tone — this is a real person's livelihood

Return only JSON: {"assistant_message": "..."}
"""

PHRASING_PROMPT = """
You are a concise intake coordinator for an Israeli employment-law firm.
You will receive the full conversation so far, the current intake state, and
the one slot the system needs to collect next.

Write a single short Hebrew response that:
- Briefly and naturally acknowledges what the user just said (skip if nothing new to acknowledge)
- Asks exactly ONE question to collect the target slot
- References information the user already provided when it makes the question feel natural
  (e.g. use their employer name when asking about duration)
- Never asks for information already filled in the known_slots
- Is concise — ideally under 15 Hebrew words
- Sounds like a real person, not a form

Special canonical messages — handle exactly as described:
- "retry_unclear_answer": the user's last answer was unclear; politely ask them to clarify
  the same question in a different way (e.g. "לא הצלחתי להבין, אפשר לפרט קצת?")
- "fallback_after_retries": ask for a phone number so the attorney can call back
  (e.g. "אשמח אם תשאיר/י מספר טלפון ועורכת הדין תחזור אליך")

Return only JSON: {"assistant_message": "..."}
"""


def extract_with_openai(
    message: str,
    last_asked_slot: str | None = None,
    last_question: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> dict[str, str]:
    if not settings.openai_api_key:
        return {}

    user_payload = {
        "user_message": message,
        "last_asked_slot": last_asked_slot,
        "last_question": last_question,
        "recent_history": (history or [])[-4:],
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
        "conversation_history": context.history[-10:],
        "selected_slot": context.next_slot,
        "canonical_message": context.canonical_message,
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
            temperature=0.4,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        message = str(data.get("assistant_message", "")).strip()
    except Exception:
        return None

    if not message or len(message) > 220:
        return None

    return message


def assess_case_with_openai(state: IntakeState) -> str | None:
    if not settings.openai_api_key:
        return None

    payload = {
        "known_slots": state.slots,
        "conversation_history": state.history[-10:],
        "turn_count": state.turn_count,
    }

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": CASE_ASSESSMENT_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        message = str(data.get("assistant_message", "")).strip()
    except Exception:
        return None

    if not message or len(message) > 350:
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
