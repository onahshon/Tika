import asyncio
import time
from uuid import uuid4

from backend.app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from backend.app.services.notifications import notify_attorney
from backend.app.services.openai_intake import converse_with_openai

_CONVERSATIONS: dict[str, dict] = {}
_NOTIFIED: set[str] = set()
_TIMESTAMPS: dict[str, float] = {}
_TTL = 2 * 60 * 60  # 2 hours


def _prune_stale() -> None:
    cutoff = time.time() - _TTL
    stale = [cid for cid, ts in _TIMESTAMPS.items() if ts < cutoff]
    for cid in stale:
        _CONVERSATIONS.pop(cid, None)
        _TIMESTAMPS.pop(cid, None)
        _NOTIFIED.discard(cid)


async def handle_chat_message(request: ChatMessageRequest) -> ChatMessageResponse:
    _prune_stale()

    conversation_id = request.conversation_id or str(uuid4())
    _TIMESTAMPS[conversation_id] = time.time()
    state = _CONVERSATIONS.setdefault(
        conversation_id,
        {"attorney_id": request.attorney_id, "history": [], "finalized": False},
    )

    if state["finalized"]:
        return ChatMessageResponse(
            conversation_id=conversation_id,
            assistant_message="כבר העברתי את הפרטים. אם יש עדכון, ניתן להשאיר הודעה.",
            notification_sent=False,
        )

    state["history"].append({"role": "user", "content": request.message})
    result = await converse_with_openai(state["history"])

    if result is None:
        reply = "מצטערת, יש תקלה זמנית. אפשר לנסות שוב בעוד רגע?"
        state["history"].append({"role": "assistant", "content": reply})
        return ChatMessageResponse(
            conversation_id=conversation_id,
            assistant_message=reply,
            notification_sent=False,
        )

    reply = result["response"]
    state["history"].append({"role": "assistant", "content": reply})

    notification_sent = False
    if result.get("ready_for_attorney") and conversation_id not in _NOTIFIED:
        transcript = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in state["history"]
        )
        notification_sent = await asyncio.to_thread(
            notify_attorney,
            subject="Tika Law — new lead",
            body=transcript,
        )
        if notification_sent:
            _NOTIFIED.add(conversation_id)
            state["finalized"] = True

    return ChatMessageResponse(
        conversation_id=conversation_id,
        assistant_message=reply,
        notification_sent=notification_sent,
    )
