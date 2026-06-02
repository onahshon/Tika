import pytest

from backend.app.schemas.intake import LeadIntakeRequest
from backend.app.services.lead_qualification import (
    HIGH_INTENT_TERMS,
    _build_follow_up_questions,
    _build_next_message,
    _classify,
    _score_lead,
)


def make_request(**overrides) -> LeadIntakeRequest:
    defaults = {
        "attorney_id": "demo-attorney",
        "full_name": "ישראל ישראלי",
        "phone": "050-0000000",
        "employment_status": "terminated",
        "issue_type": "general",
        "description": "תיאור קצר",
    }
    defaults.update(overrides)
    return LeadIntakeRequest(**defaults)


# ── _score_lead ──────────────────────────────────────────────────────────────

def test_score_baseline():
    req = make_request(phone="")
    # phone is required (min_length=1), so use a placeholder that won't add points — it always adds 10.
    # Baseline: 20 base + 10 employment_status + 10 phone = 40 minimum with required fields.
    req2 = make_request()
    score = _score_lead(req2)
    assert score >= 20


def test_score_high_intent_keyword_in_description():
    req = make_request(description="פוטרתי בלי שימוע ורוצה לתבוע")
    score = _score_lead(req)
    # base 20 + keyword 25 + employment_status 10 + phone 10 = 65
    assert score >= 65


def test_score_high_intent_keyword_in_issue_type():
    req = make_request(issue_type="harassment", description="תיאור קצר")
    score = _score_lead(req)
    assert score >= 45  # base + keyword + required fields


def test_score_all_optional_fields():
    req = make_request(
        issue_type="פיטור",
        description="א" * 120,
        employer_name="חברת ABC",
        incident_date="2024-01-01",
        desired_outcome="פיצוי",
    )
    score = _score_lead(req)
    # base 20 + keyword 25 + employment_status 10 + phone 10 + employer 10 + date 10 + outcome 5 + long desc 10 = 100
    assert score == 100


def test_score_long_description_adds_10():
    short_req = make_request(description="א" * 50)
    long_req = make_request(description="א" * 120)
    assert _score_lead(long_req) == _score_lead(short_req) + 10


def test_score_capped_at_100():
    req = make_request(
        issue_type="פיטור",
        description="א" * 200,
        employer_name="חברה",
        incident_date="2024-01-01",
        desired_outcome="פיצוי",
    )
    assert _score_lead(req) == 100


# ── _classify ────────────────────────────────────────────────────────────────

def test_classify_high_quality():
    assert _classify(70) == "high_quality"
    assert _classify(100) == "high_quality"


def test_classify_needs_review():
    assert _classify(45) == "needs_review"
    assert _classify(69) == "needs_review"


def test_classify_low_information():
    assert _classify(44) == "low_information"
    assert _classify(0) == "low_information"


# ── _build_follow_up_questions ───────────────────────────────────────────────

def test_follow_up_all_missing():
    req = make_request()  # no employer_name, incident_date, desired_outcome; short description
    questions = _build_follow_up_questions(req)
    assert len(questions) == 4


def test_follow_up_none_missing():
    req = make_request(
        employer_name="חברה",
        incident_date="2024-01-01",
        desired_outcome="פיצוי",
        description="א" * 120,
    )
    questions = _build_follow_up_questions(req)
    assert questions == []


def test_follow_up_short_description_triggers_question():
    req = make_request(
        employer_name="חברה",
        incident_date="2024-01-01",
        desired_outcome="פיצוי",
        description="קצר",
    )
    questions = _build_follow_up_questions(req)
    assert len(questions) == 1
    assert "תאר" in questions[0] or "מה קרה" in questions[0] or "תאריכים" in questions[0]


def test_follow_up_capped_at_4():
    req = make_request()  # triggers all 4 questions
    questions = _build_follow_up_questions(req)
    assert len(questions) <= 4


# ── _build_next_message ──────────────────────────────────────────────────────

def test_next_message_with_questions_always_asks_for_more():
    msg = _build_next_message("high_quality", ["שאלה 1"])
    assert "להשלים" in msg or "שאלות" in msg


def test_next_message_high_quality_no_questions():
    msg = _build_next_message("high_quality", [])
    assert "עורך הדין" in msg


def test_next_message_low_information_no_questions():
    msg = _build_next_message("low_information", [])
    assert "סקירה" in msg or "נשמרה" in msg
