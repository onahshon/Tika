import json
from typing import Any

from openai import OpenAI

from backend.app.core.config import settings
from backend.app.services.intake_engine import IntakeState, PhraseContext

EXTRACTION_PROMPT = """
You are extracting facts from a Hebrew employment-law intake conversation.

Be GENEROUS with inference — if the answer implies something, extract it:
- "קיבלתי שימוע" when asked about employment status → current_status: still_employed
  (in Israeli law, a hearing happens BEFORE termination — the person is still employed)
- "[duration] ב[place]" e.g. "שבוע בבורגר ראנץ" → employer_name: "בורגר ראנץ", employment_duration: "שבוע"
- "הם שלחו לי מייל / מכתב / הודעה" → documentation_exists: yes
- "כבר חתמתי" → signed_documents: signed
- "עדיין עובד", "עדיין שם", "ממשיך" → current_status: still_employed
- Tolerate typos, informal Hebrew, and very short answers — interpret the intent

If last_asked_slot is set, focus on that slot but extract anything else you notice too.
Use recent_history to resolve ambiguities — short answers only make sense in context.

Return only JSON (null for unknown):
{
  "employer_name": null,
  "employment_duration": null,
  "procedural_stage": null,
  "current_status": null,
  "documentation_exists": null,
  "urgency": null,
  "signed_documents": null
}

procedural_stage values: hearing_scheduled | hearing_completed | before_hearing | dismissal_stage | wage_issue | harassment_or_discrimination
current_status values: still_employed | terminated | resigned | unpaid_leave
documentation_exists values: yes | no | unclear
urgency values: immediate | near_term | dated | not_urgent | unclear
signed_documents values: signed | not_signed | requested | unclear
"""

PHRASING_PROMPT = """
You are an intake coordinator at an Israeli employment-law firm, having a real conversation with a potential client.
You have the full conversation history, what's already known, and the next slot to collect.

Write ONE short natural Hebrew response. This should feel like a real human conversation, not a form.

General style:
- Vary acknowledgments — sometimes "בסדר.", sometimes "מובן.", sometimes skip it entirely
- Use specific details the user gave (employer name, situation) to make questions feel personal
- Keep it concise — under 15 Hebrew words ideally
- Ask exactly one question at a time
- Never repeat a question that was already answered
- Never sound like a bot reading from a script

━━━ SPECIAL CASE: canonical_message = "retry_unclear_answer" ━━━

The user's last message didn't clearly answer the question.
NEVER write "לא הצלחתי להבין" — it sounds dismissive and robotic.

Instead, look at the conversation history and what the user actually said, then:

A) If the user is asking their own question ("יש לי קייס?", "כדאי לי?", "מה הסיכויים?",
   "אני בצרות?" or any similar meta-question about their situation):
   → Give an honest, brief assessment based on known_slots
   → Mention real factors: short tenure = probationary period = weaker protections;
     hearing scheduled = still active, worth consulting; etc.
   → Then guide toward next step (usually asking for phone)
   → Example: "שבוע עבודה זה עדיין תקופת ניסיון — ההגנות מוגבלות, אבל שימוע
     זה משמעותי. כדאי לבדוק עם עו״ד. תשאיר/י מספר?"

B) If the user's answer implies something but wasn't explicit ("קיבלתי שימוע" when asked
   if still employed — implies yes, still employed):
   → Confirm your interpretation and move forward
   → Example: "כלומר אתה עדיין עובד שם נכון? בוא נמשיך —"

C) If genuinely unclear:
   → Ask ONE targeted clarifying question that references what they actually said
   → Make it specific — show you read what they wrote

━━━ SPECIAL CASE: canonical_message = "fallback_after_retries" ━━━
Ask warmly for a phone number for the attorney to call back.

Return only JSON: {"assistant_message": "..."}
"""

CASE_ASSESSMENT_PROMPT = """
You are an intake coordinator at an Israeli employment-law firm.
A potential client asked whether they have a case, or something similar.

Based on the known facts and conversation history, give a brief honest assessment in Hebrew.

Be real:
- Very short tenure (days or 1-2 weeks) = probationary period in Israel = fewer legal protections. Say so honestly.
- Hearing scheduled = still employed, active situation — worth consulting before it happens
- Already terminated without due process = potentially stronger claim
- If you don't know enough yet, say so and ask what happened

Never promise outcomes. Never use legal jargon.
2-3 short sentences maximum. End by asking for their phone number.

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

    if not message or len(message) > 300:
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
