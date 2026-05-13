import re
from dataclasses import dataclass, field

CONTACT_SLOT = "contact"

QUESTION_COPY = {
    "employer_duration": "איפה אתה עובד וכמה זמן שם?",
    "employment_status": "מה הסטטוס כרגע - עדיין עובד או אחרי סיום?",
    "procedural_stage": "כבר התקיים שימוע או רק קיבלת זימון?",
    "documentation": "יש לך זימון, הודעות או מסמכים כתובים?",
    "urgency": "יש דדליין קרוב או מועד לשימוע?",
    "signed_docs": "ביקשו ממך לחתום על משהו?",
    CONTACT_SLOT: "נראה שכדאי שעו״ד יעבור על זה. אפשר טלפון לחזרה?",
}

EMPLOYMENT_TERMS = (
    "עבודה",
    "עובד",
    "מעסיק",
    "חברה",
    "שימוע",
    "פיטור",
    "שכר",
    "תלוש",
    "חופשה",
    "מילואים",
    "הריון",
    "אפליה",
    "הטרדה",
    "התפטר",
)

NOT_RELEVANT_TERMS = (
    "שכירות",
    "דירה",
    "פלילי",
    "משפחה",
    "גירושין",
    "ירושה",
    "חוב לבנק",
)


@dataclass
class IntakeState:
    conversation_id: str
    attorney_id: str
    slots: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)
    asked_counts: dict[str, int] = field(default_factory=dict)
    asked_questions: set[str] = field(default_factory=set)
    turn_count: int = 0
    finalized: bool = False


@dataclass
class IntakeDecision:
    assistant_message: str
    classification: str
    score: int
    lead_captured: bool
    suggested_next_questions: list[str]


def advance_intake(state: IntakeState, message: str) -> IntakeDecision:
    state.turn_count += 1
    state.history.append({"role": "user", "content": message})
    _merge_slots(state.slots, extract_slots(message))

    score = score_state(state)
    classification = classify_state(state, score)

    if CONTACT_SLOT in state.slots and _ready_for_review(state):
        state.finalized = True
        reply = "אוקיי. אעביר לעורך הדין סיכום קצר לבדיקה."
        state.history.append({"role": "assistant", "content": reply})
        return IntakeDecision(reply, classification, score, True, [])

    if (
        _ready_for_review(state)
        and CONTACT_SLOT not in state.slots
        and state.asked_counts.get(CONTACT_SLOT, 0) >= 1
    ):
        state.finalized = True
        reply = "אין בעיה. בלי טלפון לא אעביר למשרד כרגע."
        state.history.append({"role": "assistant", "content": reply})
        return IntakeDecision(reply, classification, score, False, [])

    if classification == "not_relevant" and state.turn_count >= 2:
        reply = "זה לא נשמע כמו דיני עבודה. יש קשר למעסיק?"
        state.history.append({"role": "assistant", "content": reply})
        return IntakeDecision(reply, classification, score, False, ["יש קשר למעסיק?"])

    next_slot = select_next_slot(state)
    if next_slot is None:
        state.finalized = True
        if _ready_for_review(state) and CONTACT_SLOT not in state.slots:
            reply = "אין בעיה. בלי טלפון לא אעביר למשרד כרגע."
        else:
            reply = "כרגע חסר מידע לבדיקה. אם יש מסמך מהמעסיק, שמור אותו."
        state.history.append({"role": "assistant", "content": reply})
        return IntakeDecision(reply, classification, score, False, [])

    question = QUESTION_COPY[next_slot]
    _mark_asked(state, next_slot, question)
    assistant_message = _prefix_for_state(state, next_slot) + question
    state.history.append({"role": "assistant", "content": assistant_message})
    return IntakeDecision(assistant_message, classification, score, False, [question])


def extract_slots(message: str) -> dict[str, str]:
    text = message.strip()
    lowered = text.lower()
    slots: dict[str, str] = {}

    if any(term in lowered for term in EMPLOYMENT_TERMS):
        slots["issue"] = text
    if any(term in lowered for term in NOT_RELEVANT_TERMS):
        slots["possible_non_employment"] = text

    employer = _extract_employer(text)
    if employer:
        slots["employer"] = employer

    duration = _extract_duration(text)
    if duration:
        slots["employment_duration"] = duration

    status = _extract_status(lowered)
    if status:
        slots["employment_status"] = status

    stage = _extract_procedural_stage(lowered)
    if stage:
        slots["procedural_stage"] = stage

    docs = _extract_documentation(lowered)
    if docs:
        slots["documentation"] = docs

    timing = _extract_timing(lowered)
    if timing:
        slots["urgency"] = timing

    signed = _extract_signed_docs(lowered)
    if signed:
        slots["signed_docs"] = signed

    contact = _extract_contact(text)
    if contact:
        slots[CONTACT_SLOT] = contact

    return slots


def select_next_slot(state: IntakeState) -> str | None:
    if (
        _ready_for_review(state)
        and CONTACT_SLOT not in state.slots
        and state.asked_counts.get(CONTACT_SLOT, 0) == 0
    ):
        return CONTACT_SLOT

    priority = [
        "employer_duration",
        "employment_status",
        "procedural_stage",
        "documentation",
        "urgency",
        "signed_docs",
    ]

    for slot in priority:
        if _slot_completed(state, slot):
            continue
        if state.asked_counts.get(slot, 0) >= 1:
            continue
        return slot

    if (
        _ready_for_review(state)
        and CONTACT_SLOT not in state.slots
        and state.asked_counts.get(CONTACT_SLOT, 0) == 0
    ):
        return CONTACT_SLOT

    return None


def score_state(state: IntakeState) -> int:
    score = 10
    slots = state.slots

    if "issue" in slots:
        score += 20
    if "employer" in slots:
        score += 15
    if "employment_duration" in slots:
        score += 10
    if "employment_status" in slots:
        score += 10
    if "procedural_stage" in slots:
        score += 15
    if "documentation" in slots:
        score += 10
    if "urgency" in slots:
        score += 10
    if CONTACT_SLOT in slots:
        score += 10

    return min(score, 100)


def classify_state(state: IntakeState, score: int) -> str:
    if "possible_non_employment" in state.slots and "issue" not in state.slots:
        return "not_relevant"
    if score >= 75:
        return "high_quality"
    if score >= 45:
        return "needs_review"
    return "low_information"


def build_summary(state: IntakeState) -> str:
    labels = {
        "issue": "Issue",
        "employer": "Employer",
        "employment_duration": "Employment duration",
        "employment_status": "Employment status",
        "procedural_stage": "Procedural stage",
        "documentation": "Documentation",
        "urgency": "Urgency/timing",
        "signed_docs": "Signed documents",
        CONTACT_SLOT: "Contact",
    }
    lines = [f"{labels[key]}: {value}" for key, value in state.slots.items() if key in labels]
    transcript = "\n".join(f"{item['role']}: {item['content']}" for item in state.history[-12:])
    return "\n".join([*lines, "", "Recent conversation:", transcript]).strip()


def _ready_for_review(state: IntakeState) -> bool:
    required_signal = [
        "issue",
        "employer",
        "employment_duration",
        "employment_status",
        "procedural_stage",
        "documentation",
        "urgency",
    ]
    completed = sum(1 for slot in required_signal if slot in state.slots)
    return completed >= 4 and state.turn_count >= 3


def _slot_completed(state: IntakeState, slot: str) -> bool:
    if slot == "employer_duration":
        return "employer" in state.slots and "employment_duration" in state.slots
    return slot in state.slots


def _mark_asked(state: IntakeState, slot: str, question: str) -> None:
    state.asked_counts[slot] = state.asked_counts.get(slot, 0) + 1
    state.asked_questions.add(question)


def _merge_slots(existing: dict[str, str], incoming: dict[str, str]) -> None:
    for key, value in incoming.items():
        if value and key not in existing:
            existing[key] = value


def _prefix_for_state(state: IntakeState, next_slot: str) -> str:
    if state.turn_count == 1 and "issue" in state.slots:
        return "מבין. "
    if next_slot == CONTACT_SLOT:
        return ""
    if "procedural_stage" in state.slots and next_slot == "documentation":
        return "אוקיי. "
    return ""


def _extract_employer(text: str) -> str | None:
    patterns = [
        r"(?:עובד|עובדת|עבדתי|אני עובד|אני עובדת)\s+(?:ב|אצל)\s+([^,.!?]+)",
        r"(?:עובד|עובדת|עבדתי|אני עובד|אני עובדת)\s+ב([^,.!? ]+)",
        r"(?:החברה|המעסיק|מקום העבודה)\s+(?:הוא|זה|בשם)?\s*([^,.!?]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            value = re.sub(r"\s*(?:שנה|שנתיים|חודש|חודשים|שנים|\d+).*$", "", value).strip()
            if 2 <= len(value) <= 80:
                return value
    return None


def _extract_duration(text: str) -> str | None:
    match = re.search(r"(\d+|שנה|שנתיים|שלוש|ארבע|חמש|שש|שבע|שמונה|תשע|עשר)\s*(?:שנים|שנה|חודשים|חודש|שבועות|שבוע)", text)
    if match:
        return match.group(0)
    for term in ("שנתיים", "חודשיים", "כמה ימים", "חצי שנה"):
        if term in text:
            return term
    return None


def _extract_status(lowered: str) -> str | None:
    if any(term in lowered for term in ("עדיין עובד", "עדיין עובדת", "ממשיך לעבוד", "ממשיכה לעבוד")):
        return "still_employed"
    if any(term in lowered for term in ("פוטרתי", "פיטרו", "אחרי פיטורים", "סיימו לי")):
        return "terminated"
    if any(term in lowered for term in ("התפטרתי", "עזבתי")):
        return "resigned"
    if any(term in lowered for term in ("חל\"ת", "חלת")):
        return "unpaid_leave"
    return None


def _extract_procedural_stage(lowered: str) -> str | None:
    if "זימון לשימוע" in lowered or "קיבלתי זימון" in lowered:
        return "hearing_scheduled"
    if "שימוע" in lowered and any(term in lowered for term in ("התקיים", "היה", "עברתי", "אחרי")):
        return "hearing_completed"
    if "לפני שימוע" in lowered:
        return "before_hearing"
    if "פיטור" in lowered:
        return "dismissal_stage"
    return None


def _extract_documentation(lowered: str) -> str | None:
    if any(term in lowered for term in ("יש לי", "קיבלתי", "שלחו לי")) and any(
        doc in lowered for doc in ("זימון", "מייל", "הודעה", "מסמך", "מכתב", "תלוש", "הקלטה")
    ):
        return "has_documents"
    if any(term in lowered for term in ("אין לי מסמך", "אין תיעוד", "בעל פה")):
        return "no_documents"
    return None


def _extract_timing(lowered: str) -> str | None:
    if any(term in lowered for term in ("אתמול", "היום", "מחר", "ביום ראשון", "ביום שני", "ביום שלישי", "ביום רביעי", "ביום חמישי", "ביום שישי")):
        return "near_term"
    if any(term in lowered for term in ("דחוף", "השבוע", "שבוע הבא", "עוד יומיים")):
        return "urgent"
    if re.search(r"\d{1,2}[./-]\d{1,2}", lowered):
        return "dated"
    return None


def _extract_signed_docs(lowered: str) -> str | None:
    if any(term in lowered for term in ("חתמתי", "כבר חתמתי")):
        return "signed"
    if any(term in lowered for term in ("לא חתמתי", "עוד לא חתמתי", "ביקשו לחתום")):
        return "not_signed_or_requested"
    return None


def _extract_contact(text: str) -> str | None:
    phone = re.search(r"05\d[-\s]?\d{7}", text)
    if phone:
        return phone.group(0)
    email = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", text)
    if email:
        return email.group(0)
    return None
