import json
from typing import Any

from openai import OpenAI

from backend.app.core.config import settings
from backend.app.services.intake_engine import IntakeState, PhraseContext

CONVERSATION_PROMPT = """
You are Tika, the digital intake assistant for an Israeli employment-law firm.
Your job: have a natural, empathetic conversation that understands the client's situation
and gathers what the attorney needs to assess the case.

You receive:
- conversation: full conversation history (latest entry is the client's most recent message)
- known_slots: facts already collected
- turn_count: how many turns have passed

━━━ RESPONSE RULES ━━━

Respond to EVERYTHING the client says — any phrasing, any emotion, any topic.
Never say "לא הבנתי" or "לא הצלחתי להבין". Always engage with what was actually written.

If the client describes abuse, harassment, violence, or discrimination at work →
acknowledge what they said with empathy before asking anything.

If the client asks "יש לי קייס?" or "כדאי לי?" or any question about their chances →
give an honest brief assessment based on known_slots:
- Very short tenure (days / 1-2 weeks) = probationary period in Israel = fewer protections. Say so honestly.
- Hearing scheduled = still employed, time-sensitive — worth consulting immediately
- Never make legal promises

━━━ INFORMATION TO COLLECT (naturally, not as a questionnaire) ━━━
- What happened (the employment issue)
- Employer name and how long they've worked there
- Still employed or already left / terminated?
- Procedural stage: hearing scheduled? hearing happened? dismissed? ongoing issue?
- Documents: emails, letters, recordings?
- Urgency: is there a deadline or hearing date?
- Contact phone — ask ONLY after turn 3+ and only once you understand the situation

━━━ STYLE ━━━
- One question per response
- Under 20 Hebrew words ideally
- Vary your phrasing — not every message needs an acknowledgment prefix
- Sound like a real person, not a form or a bot

━━━ FINALIZATION ━━━
Set ready_for_attorney: true when you have a contact number AND enough of the situation is clear.

Return ONLY this JSON:
{
  "response": "Hebrew response here",
  "extracted_slots": {
    "employer": null,
    "employment_duration": null,
    "employment_status": null,
    "procedural_stage": null,
    "documentation": null,
    "urgency": null,
    "signed_docs": null,
    "contact": null
  },
  "ready_for_attorney": false
}

employment_status values: still_employed | terminated | resigned | unpaid_leave
procedural_stage values: hearing_scheduled | hearing_completed | before_hearing | dismissal_stage | wage_issue | harassment_or_discrimination
documentation values: has_documents | no_documents
urgency values: immediate | near_term | dated | not_urgent
signed_docs values: signed | not_signed | requested
"""


def converse_with_openai(state: IntakeState) -> dict[str, Any] | None:
    if not settings.openai_api_key:
        return None

    payload = {
        "conversation": state.history,
        "known_slots": state.slots,
        "turn_count": state.turn_count,
    }

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": CONVERSATION_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        if not data.get("response"):
            return None
        return data
    except Exception:
        return None


def _map_extraction(payload: dict[str, Any]) -> dict[str, str]:
    slots: dict[str, str] = {}

    if _clean(payload.get("employer")):
        slots["employer"] = _clean(payload.get("employer"))
    if _clean(payload.get("employment_duration")):
        slots["employment_duration"] = _clean(payload.get("employment_duration"))
    if _clean(payload.get("procedural_stage")):
        slots["procedural_stage"] = _clean(payload.get("procedural_stage"))
    if _clean(payload.get("employment_status")):
        slots["employment_status"] = _clean(payload.get("employment_status"))
    if _clean(payload.get("documentation")):
        slots["documentation"] = _clean(payload.get("documentation"))
    if _clean(payload.get("urgency")):
        slots["urgency"] = _clean(payload.get("urgency"))
    if _clean(payload.get("signed_docs")):
        slots["signed_docs"] = _clean(payload.get("signed_docs"))
    if _clean(payload.get("contact")):
        slots["contact"] = _clean(payload.get("contact"))

    return slots


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
