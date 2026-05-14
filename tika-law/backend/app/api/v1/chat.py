from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.v1.dependencies import require_attorney_id
from backend.app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ContactSubmitRequest,
    ContactSubmitResponse,
)
from backend.app.services.ai_chat import handle_chat_message, submit_contact

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
async def create_chat_message(
    request: ChatMessageRequest,
    attorney_id: str = Depends(require_attorney_id),
) -> ChatMessageResponse:
    if request.attorney_id != attorney_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="attorney_id must match X-Attorney-Id.",
        )
    return await handle_chat_message(request)


@router.post("/contact", response_model=ContactSubmitResponse)
async def submit_contact_details(
    request: ContactSubmitRequest,
    attorney_id: str = Depends(require_attorney_id),
) -> ContactSubmitResponse:
    if request.attorney_id != attorney_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="attorney_id must match X-Attorney-Id.",
        )
    return await submit_contact(
        request.conversation_id,
        request.name,
        request.phone,
        request.email,
    )
