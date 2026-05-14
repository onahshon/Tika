import asyncio
import time
from uuid import uuid4

from backend.app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from backend.app.services.intake_engine import (
    IntakeState,
    build_summary,
    classify_state,
    score_state,
)
from backend.app.services.notifications import notify_attorney
from backend.app.services.openai_intake import converse_with_openai

CONVERSATIONS: dict[str, IntakeState] = {}
NOTIFIED_CONVERSATIONS: set[str] = set()
_TIMESTAMPS: dict[str, float] = {}
_TTL = 2 * 60 * 60  # 2 hours


def _prune_stale() -> None:
    cutoff = time.time() - _TTL
    stale = [cid for cid, ts in _TIMESTAMPS.items() if ts < cutoff]
    for cid in stale:
        CONVERSATIONS.pop(cid, None)
        _TIMESTAMPS.pop(cid, None)
        NOTIFIED_CONVERSATIONS.discard(cid)


async def handle_chat_message(request: ChatMessageRequest) -> ChatMessageResponse:
    _prune_stale()

    conversation_id = request.conversation_id or str(uuid4())
    _TIMESTAMPS[conversation_id] = time.time()
    state = CONVERSATIONS.setdefault(
        conversation_id,
        IntakeState(conversation_id=conversation_id, attorney_id=request.attorney_id),
    )

    if state.finalized:
        return ChatMessageResponse(
            conversation_id=conversation_id,
            assistant_message="כבר העברתי את הפרטים. אם יש עדכון, ניתן להשאיר הודעה.",
            classification="finalized",
            score=score_state(state),
            lead_captured=False,
            notification_sent=False,
            suggested_next_questions=[],
        )

    state.turn_count += 1
    state.history.append({"role": "user", "content": request.message})

    result = await converse_with_openai(state)

    if result is None:
        reply = "מצטערת, יש תקלה זמנית. אפשר לנסות שוב בעוד רגע?"
        state.history.append({"role": "assistant", "content": reply})
        return ChatMessageResponse(
            conversation_id=conversation_id,
            assistant_message=reply,
            classification="low_information",
            score=score_state(state),
            lead_captured=False,
            notification_sent=False,
            suggested_next_questions=[],
        )

    for key, value in (result.get("extracted_slots") or {}).items():
        if value and key not in state.slots:
            state.slots[key] = str(value)

    reply = result["response"]
    state.history.append({"role": "assistant", "content": reply})

    score = score_state(state)
    classification = classify_state(state, score)
    lead_captured = bool(state.slots.get("contact")) and result.get("ready_for_attorney", False)
    notification_sent = False

    if lead_captured and conversation_id not in NOTIFIED_CONVERSATIONS:
        notification_sent = await asyncio.to_thread(
            notify_attorney,
            subject=f"Tika Law lead: {classification} ({score}/100)",
            body=build_summary(state),
        )
        if notification_sent:
            NOTIFIED_CONVERSATIONS.add(conversation_id)
            state.finalized = True

    return ChatMessageResponse(
        conversation_id=conversation_id,
        assistant_message=reply,
        classification=classification,
        score=score,
        lead_captured=lead_captured,
        notification_sent=notification_sent,
        suggested_next_questions=[],
    )
