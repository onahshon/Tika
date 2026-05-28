import asyncio
import logging
import time
from uuid import uuid4

from backend.app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ContactSubmitResponse,
)
from backend.app.services.notifications import notify_attorney
from backend.app.services.openai_intake import converse_with_openai

logger = logging.getLogger(__name__)


_CONVERSATIONS: dict[str, dict] = {}
_TIMESTAMPS: dict[str, float] = {}
_TTL = 2 * 60 * 60  # 2 hours
_TRANSCRIPT_LABELS = {
    "user": "לקוח/ה",
    "assistant": "טיקה",
}


def _prune_stale() -> None:
    cutoff = time.time() - _TTL
    stale = [cid for cid, ts in _TIMESTAMPS.items() if ts < cutoff]
    for cid in stale:
        _CONVERSATIONS.pop(cid, None)
        _TIMESTAMPS.pop(cid, None)


async def handle_chat_message(request: ChatMessageRequest) -> ChatMessageResponse:
    _prune_stale()

    conversation_id = request.conversation_id or str(uuid4())
    _TIMESTAMPS[conversation_id] = time.time()
    state = _CONVERSATIONS.setdefault(
        conversation_id,
        {
            "attorney_id": request.attorney_id,
            "history": [],
            "finalized": False,
            "form_shown": False,
        },
    )

    if state["finalized"]:
        return ChatMessageResponse(
            conversation_id=conversation_id,
            assistant_message="כבר העברתי את הפרטים. אם יש עדכון, ניתן להשאיר הודעה.",
        )

    state["history"].append({"role": "user", "content": request.message})
    result = await converse_with_openai(state["history"])

    if result is None:
        reply = "מצטערת, יש תקלה זמנית. אפשר לנסות שוב בעוד רגע?"
        state["history"].append({"role": "assistant", "content": reply})
        return ChatMessageResponse(
            conversation_id=conversation_id,
            assistant_message=reply,
        )

    reply = result["response"]
    state["history"].append({"role": "assistant", "content": reply})

    # Show the contact form exactly once — the first time the AI is ready
    show_form = False
    if result.get("ready_for_attorney") and not state["finalized"] and not state["form_shown"]:
        state["form_shown"] = True
        show_form = True

    return ChatMessageResponse(
        conversation_id=conversation_id,
        assistant_message=reply,
        show_contact_form=show_form,
    )


async def submit_contact(
    attorney_id: str,
    conversation_id: str,
    name: str,
    phone: str,
    email: str | None,
) -> ContactSubmitResponse:
    state = _CONVERSATIONS.get(conversation_id)

    if state and state["finalized"]:
        return ContactSubmitResponse(success=False)

    transcript = _build_transcript(state["history"]) if state else ""

    sent = await asyncio.to_thread(
        notify_attorney,
        attorney_id=attorney_id,
        name=name,
        phone=phone,
        email=email,
        transcript=transcript,
    )

    if sent and state:
        state["finalized"] = True

    return ContactSubmitResponse(success=sent)


def _build_transcript(history: list[dict]) -> str:
    lines = []
    for message in history:
        role = _TRANSCRIPT_LABELS.get(message["role"], message["role"])
        lines.append(f"{role}: {message['content']}")

    return "\n".join(lines)
