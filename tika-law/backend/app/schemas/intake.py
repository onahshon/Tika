from pydantic import BaseModel, EmailStr, Field


class LeadIntakeRequest(BaseModel):
    attorney_id: str = Field(min_length=1)
    full_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=40)
    email: EmailStr | None = None
    employment_status: str = Field(min_length=1, max_length=80)
    issue_type: str = Field(min_length=1, max_length=120)
    employer_name: str | None = Field(default=None, max_length=160)
    incident_date: str | None = Field(default=None, max_length=80)
    desired_outcome: str | None = Field(default=None, max_length=300)
    description: str = Field(min_length=10, max_length=2500)


class LeadQualificationResponse(BaseModel):
    conversation_id: str
    attorney_id: str
    classification: str
    score: int
    summary: str
    follow_up_questions: list[str]
    next_message: str
    disclaimer: str
