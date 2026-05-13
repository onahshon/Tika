import json
import re
from uuid import uuid4

from openai import OpenAI

from backend.app.core.config import settings
from backend.app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from backend.app.services.notifications import notify_attorney

SYSTEM_PROMPT = """
You are Tika Law, a Hebrew-first AI intake coordinator for an Israeli employment-law attorney.
You should feel like an experienced, human legal intake professional at a law office.

Core behavior:
- Understand first, collect contact details later.
- Do not behave like a form, a lead-capture bot, or a scripted decision tree.
- Start by understanding what happened, the employment relationship, timing, documents, and current procedural stage.
- Ask one natural follow-up question at a time, or two only when they are tightly related.
- React to the user's emotional tone with calm professionalism.
- Use varied human Hebrew phrasing. Avoid repetitive phrases like "תודה, הבנתי" and generic chatbot language.

Early conversation priorities:
- What happened?
- How long did they work there?
- Was there a hearing ("שימוע")?
- Were they dismissed, still employed, resigned, or before a decision?
- What type of employer/workplace is involved?
- Do they have written documentation, messages, salary slips, a hearing invitation, dismissal letter, or agreement?
- How urgent is it and what stage is it in right now?

Contact collection:
- Never ask for phone, email, name, or callback details at the beginning.
- Ask for callback details only after enough context exists and the matter appears relevant or potentially high-quality.
- A good callback prompt: "נראה שכדאי שעורך דין יעבור על הפרטים. אפשר מספר טלפון לחזרה?"

Allowed light procedural guidance:
- You may cautiously suggest keeping written records, saving salary slips, collecting messages, and avoiding signing documents immediately before review.
- Use cautious language: "ייתכן שכדאי", "לעיתים כדאי", "נראה שכדאי שעורך דין יעבור על זה".

Strict limits:
- Never provide legal conclusions.
- Never determine rights.
- Never promise outcomes.
- Never say "יש לך קייס" or equivalent.
- Never create an attorney-client relationship.
- Do not repeat disclaimers in every message. Use them sparingly and naturally.

Qualification:
- Classify naturally based on relevance, specificity, urgency, documentation, procedural stage, and contact availability only near the end.
- If clearly not employment law, politely explain that the office may not be the right fit and ask if there is any workplace/employer connection.

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
    user_turns = sum(1 for item in history if item["role"] == "user")
    score = _score_transcript(transcript)
    has_contact = _has_contact(transcript)
    is_employment = any(term.lower() in transcript.lower() for term in EMPLOYMENT_TERMS)
    ready_for_contact = is_employment and score >= 65 and user_turns >= 3

    if not is_employment and len(history) >= 3:
        return {
            "assistant_message": "ממה שתיארת עד עכשיו, אני לא בטוחה שזה שייך לדיני עבודה. יש כאן קשר למעסיק, שכר, פיטורים, שימוע או תנאי עבודה?",
            "classification": "not_relevant",
            "score": 20,
            "lead_captured": False,
            "suggested_next_questions": ["יש קשר למקום עבודה או למעסיק?"],
        }

    if has_contact and score >= 70 and user_turns >= 3:
        return {
            "assistant_message": "נראה שכדאי שעורך דין יעבור על הפרטים. אעביר את הסיכום לבדיקה במשרד, בלי לקבוע מסקנה משפטית בשלב הזה.",
            "classification": "high_quality",
            "score": score,
            "lead_captured": True,
            "suggested_next_questions": [],
        }

    if ready_for_contact and not has_contact:
        questions = ["אפשר מספר טלפון לחזרה, כדי שעורך הדין יוכל לבדוק את הפרטים?"]
    else:
        questions = _context_questions(transcript, user_turns)

    return {
        "assistant_message": _build_fallback_message(transcript, questions, ready_for_contact),
        "classification": "needs_review" if score >= 45 else "low_information",
        "score": score,
        "lead_captured": has_contact and score >= 65 and user_turns >= 3,
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


def _context_questions(transcript: str, user_turns: int) -> list[str]:
    questions: list[str] = []

    if user_turns <= 1:
        questions.append("כמה זמן עבדת שם, ומה הסטטוס כרגע - עדיין עובד, לפני שימוע, אחרי שימוע או אחרי פיטורים?")
    if "שימוע" not in transcript and any(word in transcript for word in ("פיטור", "לפטר", "הודיעו", "סיום")):
        questions.append("כבר התקיים שימוע או שקיבלת רק זימון?")
    if not re.search(r"\d", transcript):
        questions.append("מתי זה קרה בערך?")
    if not any(word in transcript for word in ("הודעה", "מייל", "מסמך", "תלוש", "הקלטה", "מכתב")):
        questions.append("יש לך תיעוד כתוב, הודעות, תלושי שכר או מסמך מהמעסיק?")
    if not any(word in transcript for word in ("חתמתי", "חתימה", "הסכם", "ויתור")):
        questions.append("ביקשו ממך לחתום על משהו או שכבר חתמת?")
    if not any(word in transcript for word in ("דחוף", "מחר", "היום", "שבוע", "זימון")):
        questions.append("באיזה שלב זה נמצא כרגע, והאם יש דדליין קרוב?")

    return questions[:2]


def _build_fallback_message(transcript: str, questions: list[str], ready_for_contact: bool) -> str:
    if ready_for_contact:
        return questions[0]

    if not questions:
        return "נשמע שיש כאן כמה פרטים שכדאי לסדר לפני בדיקה. ייתכן שכדאי לשמור בינתיים הודעות, מסמכים ותלושי שכר, ולא לחתום על מסמכים חדשים לפני שעוברים עליהם."

    first_sentence = "אני רוצה להבין את השלב המדויק לפני שמחליטים אם להעביר לבדיקה."
    if any(word in transcript for word in ("פיטור", "שימוע", "שכר", "מעסיק")):
        first_sentence = "זה נשמע כמו עניין שיכול להיות רלוונטי לדיני עבודה, אבל צריך להבין את השלב והמסמכים."

    return f"{first_sentence} {questions[0]}"


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
