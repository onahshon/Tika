import asyncio
import time
from uuid import uuid4

from backend.app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ContactSubmitResponse,
)
from backend.app.services.notifications import notify_attorney
from backend.app.services.openai_intake import converse_with_openai

_CONVERSATIONS: dict[str, dict] = {}
_TIMESTAMPS: dict[str, float] = {}
_TTL = 2 * 60 * 60  # 2 hours


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
    conversation_id: str,
    name: str,
    phone: str,
    email: str | None,
) -> ContactSubmitResponse:
    state = _CONVERSATIONS.get(conversation_id)

    if not state or state["finalized"]:
        return ContactSubmitResponse(success=False)

    contact_lines = [f"שם: {name}", f"טלפון: {phone}"]
    if email:
        contact_lines.append(f"אימייל: {email}")

    transcript = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}" for m in state["history"]
    )

    body = "\n".join(contact_lines) + "\n\n---\n\n" + transcript

    sent = await asyncio.to_thread(
        notify_attorney,
        subject=f"Tika Law — ליד חדש: {name}",
        body=body,
    )

    if sent:
        state["finalized"] = True

    return ContactSubmitResponse(success=sent)
