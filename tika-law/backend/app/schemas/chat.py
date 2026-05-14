from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    attorney_id: str = Field(min_length=1)
    conversation_id: str | None = None
    message: str = Field(min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    conversation_id: str
    assistant_message: str
    show_contact_form: bool = False


class ContactSubmitRequest(BaseModel):
    attorney_id: str = Field(min_length=1)
    conversation_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=40)
    email: str | None = Field(default=None, max_length=200)


class ContactSubmitResponse(BaseModel):
    success: bool
