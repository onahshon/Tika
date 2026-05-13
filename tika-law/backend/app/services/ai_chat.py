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

    extracted_slots = {} if is_gibberish(request.message) else extract_with_openai(request.message)
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
    if not has_hebrew and not has_digit:
        return True

    compact = re.sub(r"\s+", "", lowered)
    unique_chars = set(compact)
    if len(compact) >= 3 and len(unique_chars) <= 2:
        return True

    return False
