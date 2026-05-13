from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.v1.dependencies import require_attorney_id
from backend.app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from backend.app.services.ai_chat import handle_chat_message

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
def create_chat_message(
    request: ChatMessageRequest,
    attorney_id: str = Depends(require_attorney_id),
) -> ChatMessageResponse:
    if request.attorney_id != attorney_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="attorney_id must match X-Attorney-Id.",
        )

    return handle_chat_message(request)
