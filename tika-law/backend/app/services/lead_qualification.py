from uuid import uuid4

from backend.app.schemas.intake import LeadIntakeRequest, LeadQualificationResponse

HIGH_INTENT_TERMS = (
    "פיטור",
    "שימוע",
    "שכר",
    "הלנת",
    "הטרדה",
    "אפליה",
    "הריון",
    "מילואים",
    "termination",
    "salary",
    "wage",
    "harassment",
    "discrimination",
)

CONVERSATIONS: dict[str, LeadQualificationResponse] = {}


def qualify_lead(request: LeadIntakeRequest) -> LeadQualificationResponse:
    score = _score_lead(request)
    classification = _classify(score)
    questions = _build_follow_up_questions(request)
    conversation_id = str(uuid4())

    response = LeadQualificationResponse(
        conversation_id=conversation_id,
        attorney_id=request.attorney_id,
        classification=classification,
        score=score,
        summary=_build_summary(request),
        follow_up_questions=questions,
        next_message=_build_next_message(classification, questions),
        disclaimer="המערכת אוספת מידע ראשוני בלבד ואינה מספקת ייעוץ משפטי.",
    )
    CONVERSATIONS[conversation_id] = response
    return response


def _score_lead(request: LeadIntakeRequest) -> int:
    score = 20
    combined_text = f"{request.issue_type} {request.description}".lower()

    if any(term.lower() in combined_text for term in HIGH_INTENT_TERMS):
        score += 25
    if request.employment_status:
        score += 10
    if request.phone:
        score += 10
    if request.employer_name:
        score += 10
    if request.incident_date:
        score += 10
    if request.desired_outcome:
        score += 5
    if len(request.description.strip()) >= 120:
        score += 10

    return min(score, 100)


def _classify(score: int) -> str:
    if score >= 70:
        return "high_quality"
    if score >= 45:
        return "needs_review"
    return "low_information"


def _build_follow_up_questions(request: LeadIntakeRequest) -> list[str]:
    questions: list[str] = []

    if not request.employer_name:
        questions.append("מה שם המעסיק או מקום העבודה?")
    if not request.incident_date:
        questions.append("מתי התרחש האירוע המרכזי או מתי הסתיימה ההעסקה?")
    if not request.desired_outcome:
        questions.append("מה היית רוצה להשיג בשלב הזה: פיצוי, מכתב, שיחה עם עורך דין או משהו אחר?")
    if len(request.description.strip()) < 120:
        questions.append("אפשר לתאר בקצרה מה קרה, כולל תאריכים, סכומים או מסמכים קיימים?")

    return questions[:4]


def _build_summary(request: LeadIntakeRequest) -> str:
    parts = [
        f"שם: {request.full_name}",
        f"טלפון: {request.phone}",
        f"סטטוס העסקה: {request.employment_status}",
        f"סוג עניין: {request.issue_type}",
        f"תיאור: {request.description}",
    ]

    if request.email:
        parts.insert(2, f"אימייל: {request.email}")
    if request.employer_name:
        parts.append(f"מעסיק: {request.employer_name}")
    if request.incident_date:
        parts.append(f"מועד רלוונטי: {request.incident_date}")
    if request.desired_outcome:
        parts.append(f"מטרה: {request.desired_outcome}")

    return "\n".join(parts)


def _build_next_message(classification: str, questions: list[str]) -> str:
    if questions:
        return "תודה. כדי להעביר לעורך הדין תמונה ברורה יותר, כדאי להשלים את השאלות הבאות."

    if classification == "high_quality":
        return "תודה. נראה שיש כאן פנייה עם מידע ראשוני מספק להעברה לעורך הדין."

    return "תודה. הפנייה נשמרה לסקירה ראשונית של עורך הדין."
