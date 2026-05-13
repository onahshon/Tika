import json
import re
from uuid import uuid4

from openai import OpenAI

from backend.app.core.config import settings
from backend.app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from backend.app.services.notifications import notify_attorney

SYSTEM_PROMPT = """
You are Tika Law, a Hebrew-first AI legal intake secretary for an Israeli employment-law attorney.
You are warm, concise, and professional. You feel like a capable legal secretary, not a generic chatbot.

Your job:
- collect lead qualification details through chat
- ask one or two structured follow-up questions at a time
- identify whether this is likely an employment-law lead
- collect name, phone/email, employer, employment status, issue, dates, and desired outcome
- never provide legal advice, legal conclusions, rights analysis, or promises
- if the matter is clearly unrelated to employment law, explain politely that the office may not be the best fit
- if the lead looks relevant and contact details exist, say the details can be passed to the attorney

Return only compact JSON with:
assistant_message: Hebrew response to the user
classification: one of high_quality, needs_review, low_information, not_relevant
score: integer 0-100
lead_captured: boolean
suggested_next_questions: array of short Hebrew questions
"""

EMPLOYMENT_TERMS = (
    "פיטור",
    "שימוע",
    "שכר",
    "הלנת",
    "מעסיק",
    "עבודה",
    "התפטר",
    "הטרדה",
    "אפליה",
    "הריון",
    "מילואים",
    "חופשה",
    "פנסיה",
    "termination",
    "salary",
    "employer",
    "work",
    "harassment",
    "discrimination",
)

CONVERSATIONS: dict[str, list[dict[str, str]]] = {}
NOTIFIED_CONVERSATIONS: set[str] = set()


def handle_chat_message(request: ChatMessageRequest) -> ChatMessageResponse:
    conversation_id = request.conversation_id or str(uuid4())
    history = CONVERSATIONS.setdefault(conversation_id, [])
    history.append({"role": "user", "content": request.message})

    try:
        result = _ask_openai(history) if settings.openai_api_key else _fallback_reply(history)
    except Exception:
        result = _fallback_reply(history)
    assistant_message = str(result.get("assistant_message", "")).strip()
    classification = str(result.get("classification", "needs_review"))
    score = int(result.get("score", 45))
    lead_captured = bool(result.get("lead_captured", False))
    suggested_next_questions = [str(item) for item in result.get("suggested_next_questions", [])][:3]

    notification_sent = False
    if lead_captured and classification in {"high_quality", "needs_review"} and conversation_id not in NOTIFIED_CONVERSATIONS:
        notification_sent = notify_attorney(
            subject=f"Tika Law lead: {classification} ({score}/100)",
            body=_build_notification_body(request.attorney_id, conversation_id, history, assistant_message),
        )
        if notification_sent:
            NOTIFIED_CONVERSATIONS.add(conversation_id)

    history.append({"role": "assistant", "content": assistant_message})

    return ChatMessageResponse(
        conversation_id=conversation_id,
        assistant_message=assistant_message,
        classification=classification,
        score=score,
        lead_captured=lead_captured,
        notification_sent=notification_sent,
        suggested_next_questions=suggested_next_questions,
    )


def _ask_openai(history: list[dict[str, str]]) -> dict[str, object]:
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, *history[-12:]],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def _fallback_reply(history: list[dict[str, str]]) -> dict[str, object]:
    transcript = "\n".join(item["content"] for item in history)
    latest = history[-1]["content"]
    score = _score_transcript(transcript)
    has_contact = _has_contact(transcript)
    is_employment = any(term.lower() in transcript.lower() for term in EMPLOYMENT_TERMS)

    if not is_employment and len(history) >= 3:
        return {
            "assistant_message": "תודה על הפרטים. לפי מה שתיארת, ייתכן שזה לא תחום דיני עבודה. אם יש קשר למעסיק, שכר, פיטורים או תנאי עבודה, אשמח שתכתוב לי מה הקשר.",
            "classification": "not_relevant",
            "score": 20,
            "lead_captured": False,
            "suggested_next_questions": ["האם זה קשור למקום עבודה או למעסיק?"],
        }

    if has_contact and score >= 70:
        return {
            "assistant_message": "תודה, קיבלתי תמונה ראשונית טובה. אעביר את הפרטים לעורך הדין לבדיקה. חשוב לציין שזה איסוף מידע ראשוני בלבד ולא ייעוץ משפטי.",
            "classification": "high_quality",
            "score": score,
            "lead_captured": True,
            "suggested_next_questions": [],
        }

    questions = _missing_questions(transcript)
    return {
        "assistant_message": _build_fallback_message(latest, questions),
        "classification": "needs_review" if score >= 45 else "low_information",
        "score": score,
        "lead_captured": has_contact and score >= 55,
        "suggested_next_questions": questions,
    }


def _score_transcript(transcript: str) -> int:
    score = 20
    lowered = transcript.lower()
    if any(term.lower() in lowered for term in EMPLOYMENT_TERMS):
        score += 25
    if _has_contact(transcript):
        score += 20
    if re.search(r"\d", transcript):
        score += 10
    if len(transcript) > 280:
        score += 15
    if any(word in lowered for word in ("פיצוי", "תביעה", "מכתב", "שיחה", "עו\"ד", "עורך דין")):
        score += 10
    return min(score, 100)


def _has_contact(text: str) -> bool:
    has_phone = bool(re.search(r"05\d[-\s]?\d{7}", text))
    has_email = bool(re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", text))
    return has_phone or has_email


def _missing_questions(transcript: str) -> list[str]:
    questions: list[str] = []
    if not _has_contact(transcript):
        questions.append("מה מספר הטלפון או האימייל שבו עורך הדין יוכל לחזור אליך?")
    if "מעסיק" not in transcript and "חברה" not in transcript:
        questions.append("מה שם המעסיק או מקום העבודה?")
    if not re.search(r"\d", transcript):
        questions.append("מתי זה קרה בערך?")
    if not any(word in transcript for word in ("פיצוי", "מכתב", "שיחה", "תביעה")):
        questions.append("מה היית רוצה להשיג בשלב הזה?")
    return questions[:2]


def _build_fallback_message(latest: str, questions: list[str]) -> str:
    if not questions:
        return "תודה, זה עוזר. אאסוף עוד פרט קטן כדי להעביר לעורך הדין תמונה מסודרת. האם יש מסמך או הודעה שקשורים לאירוע?"
    joined = " ".join(questions)
    return f"תודה, הבנתי. כדי לבדוק התאמה ראשונית לדיני עבודה, אשמח לעוד פרט: {joined}"


def _build_notification_body(
    attorney_id: str,
    conversation_id: str,
    history: list[dict[str, str]],
    assistant_message: str,
) -> str:
    lines = [
        f"Attorney ID: {attorney_id}",
        f"Conversation ID: {conversation_id}",
        "",
        "Conversation:",
    ]
    lines.extend(f"{item['role']}: {item['content']}" for item in history)
    lines.extend(["assistant: " + assistant_message, "", "This is not legal advice."])
    return "\n".join(lines)
