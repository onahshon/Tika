from dataclasses import dataclass, field

CONTACT_SLOT = "contact"


@dataclass
class IntakeState:
    conversation_id: str
    attorney_id: str
    slots: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)
    turn_count: int = 0
    finalized: bool = False


def score_state(state: IntakeState) -> int:
    score = 10
    slots = state.slots

    if "issue_type" in slots or "issue" in slots:
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
    if score >= 75:
        return "high_quality"
    if score >= 45:
        return "needs_review"
    return "low_information"


def build_summary(state: IntakeState) -> str:
    labels = {
        "side": "Side",
        "issue_type": "Issue type",
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
    lines = [f"{labels.get(key, key)}: {value}" for key, value in state.slots.items() if value]
    transcript = "\n".join(
        f"{item['role']}: {item['content']}" for item in state.history[-12:]
    )
    return "\n".join([*lines, "", "Recent conversation:", transcript]).strip()
