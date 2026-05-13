from uuid import uuid4
import re

from backend.app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from backend.app.services.intake_engine import (
    IntakeState,
    advance_intake,
    build_summary,
)
from backend.app.services.notifications import notify_attorney
from backend.app.services.openai_intake import extract_with_openai, phrase_with_openai

CONVERSATIONS: dict[str, IntakeState] = {}
NOTIFIED_CONVERSATIONS: set[str] = set()


def handle_chat_message(request: ChatMessageRequest) -> ChatMessageResponse:
    conversation_id = request.conversation_id or str(uuid4())
    state = CONVERSATIONS.setdefault(
        conversation_id,
        IntakeState(conversation_id=conversation_id, attorney_id=request.attorney_id),
    )

    intent = classify_intent(request.message, state)
    if intent in {"greeting", "irrelevant_nonsense", "contact_detail", "request_human", "stop_exit"}:
        return _handle_pre_intake_intent(conversation_id, state, request.message, intent)

    last_question = _last_assistant_message(state)
    extracted_slots = (
        {}
        if is_gibberish(request.message)
        else extract_with_openai(
            request.message,
            last_asked_slot=state.last_asked_slot,
            last_question=last_question,
        )
    )
    decision = advance_intake(
        state,
        request.message,
        external_slots=extracted_slots,
        phrase_fn=phrase_with_openai,
    )

    notification_sent = False
    if decision.lead_captured and conversation_id not in NOTIFIED_CONVERSATIONS:
        notification_sent = notify_attorney(
            subject=f"Tika Law lead: {decision.classification} ({decision.score}/100)",
            body=build_summary(state),
        )
        if notification_sent:
            NOTIFIED_CONVERSATIONS.add(conversation_id)

    return ChatMessageResponse(
        conversation_id=conversation_id,
        assistant_message=decision.assistant_message,
        classification=decision.classification,
        score=decision.score,
        lead_captured=decision.lead_captured,
        notification_sent=notification_sent,
        suggested_next_questions=decision.suggested_next_questions,
    )


def classify_intent(message: str, state: IntakeState) -> str:
    text = message.strip()
    lowered = text.lower()

    if lowered in {"היי", "שלום", "הלו", "בוקר טוב", "ערב טוב", "צהריים טובים", "hi", "hello"}:
        return "greeting"

    if any(term in lowered for term in ("בן אדם", "נציג", "עורך דין", "עו\"ד", "תחזרו אלי", "תתקשרו")):
        return "request_human"

    if lowered in {"ביי", "תודה ביי", "לא משנה", "עזוב", "עזבי", "סגור"}:
        return "stop_exit"

    if _extract_contact_local(text):
        return "contact_detail"

    if state.last_asked_slot:
        return "answer_to_current_intake_question"

    if _has_legal_context(lowered):
        return "legal_situation_description"

    if is_gibberish(text) or _looks_vague_without_context(lowered):
        return "irrelevant_nonsense"

    return "irrelevant_nonsense"


def is_gibberish(message: str) -> bool:
    text = message.strip()
    lowered = text.lower()
    common_words = {"כן", "לא", "yes", "no", "ok", "okay", "אוקיי"}

    if len(text) < 2:
        return True
    if lowered in common_words:
        return False

    has_hebrew = bool(re.search(r"[\u0590-\u05ff]", text))
    has_digit = bool(re.search(r"\d", text))

    compact = re.sub(r"\s+", "", lowered)
    unique_chars = set(compact)
    if len(compact) >= 3 and len(unique_chars) == 1:
        return True

    if not has_hebrew and not has_digit and len(unique_chars) <= 2:
        return True

    return False


def _handle_pre_intake_intent(
    conversation_id: str,
    state: IntakeState,
    message: str,
    intent: str,
) -> ChatMessageResponse:
    state.turn_count += 1
    state.history.append({"role": "user", "content": message})

    if intent == "greeting":
        assistant_message = "שלום. ספר/י בקצרה מה קרה בעבודה."
        state.retry_count = 0
    elif intent == "request_human":
        assistant_message = "אפשר להשאיר טלפון, ונבדוק חזרה מהמשרד."
        state.last_asked_slot = "contact"
    elif intent == "contact_detail":
        assistant_message = "קיבלתי. כדי להבין אם מתאים להעביר למשרד, מה קרה בעבודה?"
    elif intent == "stop_exit":
        assistant_message = "אין בעיה. אם תרצה/י להמשיך, אני כאן."
        state.finalized = True
    else:
        state.retry_count += 1
        if state.retry_count >= 2:
            assistant_message = "נראה שאין מספיק מידע לבדיקה ראשונית."
            state.finalized = True
        else:
            assistant_message = "לא בטוח שהבנתי. מה קרה בעבודה?"

    state.history.append({"role": "assistant", "content": assistant_message})
    return ChatMessageResponse(
        conversation_id=conversation_id,
        assistant_message=assistant_message,
        classification="low_information",
        score=0,
        lead_captured=False,
        notification_sent=False,
        suggested_next_questions=[],
    )


def _has_legal_context(lowered: str) -> bool:
    employment_terms = (
        "שימוע",
        "פיטור",
        "פיטרו",
        "פוטרתי",
        "שכר",
        "משכורת",
        "מעסיק",
        "עבודה",
        "תלוש",
        "חופשה",
        "הריון",
        "מילואים",
        "אפליה",
        "הטרדה",
        "התפטרתי",
        "הוריד לי",
        "לא שילמו",
    )
    return any(term in lowered for term in employment_terms)


def _looks_vague_without_context(lowered: str) -> bool:
    if lowered in {"כן", "לא", "טוב", "אוקיי", "בסדר", "עובד", "חודשיים"}:
        return True
    return len(lowered.split()) <= 2


def _extract_contact_local(text: str) -> str | None:
    phone = re.search(r"05\d[-\s]?\d{7}", text)
    if phone:
        return phone.group(0)
    email = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", text)
    if email:
        return email.group(0)
    return None


def _last_assistant_message(state: IntakeState) -> str | None:
    for item in reversed(state.history):
        if item.get("role") == "assistant":
            return item.get("content")
    return None
