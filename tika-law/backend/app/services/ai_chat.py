from uuid import uuid4

from backend.app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from backend.app.services.intake_engine import (
    IntakeState,
    advance_intake,
    build_summary,
)
from backend.app.services.notifications import notify_attorney

CONVERSATIONS: dict[str, IntakeState] = {}
NOTIFIED_CONVERSATIONS: set[str] = set()


def handle_chat_message(request: ChatMessageRequest) -> ChatMessageResponse:
    conversation_id = request.conversation_id or str(uuid4())
    state = CONVERSATIONS.setdefault(
        conversation_id,
        IntakeState(conversation_id=conversation_id, attorney_id=request.attorney_id),
    )

    decision = advance_intake(state, request.message)

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
