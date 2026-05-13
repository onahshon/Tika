from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    attorney_id: str = Field(min_length=1)
    conversation_id: str | None = None
    message: str = Field(min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    conversation_id: str
    assistant_message: str
    classification: str
    score: int
    lead_captured: bool
    notification_sent: bool
    suggested_next_questions: list[str]
