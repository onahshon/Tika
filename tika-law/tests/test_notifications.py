import html as html_stdlib

from backend.app.services.notifications import (
    _build_html_body,
    _build_text_body,
    _html_line,
    _rtl_line,
)

RLM = "‏"


# ── _rtl_line ────────────────────────────────────────────────────────────────

def test_rtl_line_prepends_rlm():
    assert _rtl_line("שלום") == f"{RLM}שלום"


def test_rtl_line_empty_string():
    assert _rtl_line("") == RLM


# ── _html_line ───────────────────────────────────────────────────────────────

def test_html_line_contains_content():
    result = _html_line("שם: ישראל")
    assert "שם: ישראל" in result


def test_html_line_escapes_html():
    result = _html_line("<script>alert(1)</script>")
    assert "<script>" not in result
    assert html_stdlib.escape("<script>alert(1)</script>") in result


def test_html_line_has_rtl_direction():
    result = _html_line("טקסט")
    assert 'dir="rtl"' in result
    assert "direction:rtl" in result


# ── _build_text_body ─────────────────────────────────────────────────────────

def test_text_body_contains_contact_lines():
    body = _build_text_body(["שם: דן", "טלפון: 050"], "")
    assert "שם: דן" in body
    assert "טלפון: 050" in body


def test_text_body_contains_transcript_when_provided():
    body = _build_text_body(["שם: דן"], "לקוח/ה: שלום\nTiqa: מה הבעיה?")
    assert "תמלול" in body
    assert "שלום" in body


def test_text_body_omits_transcript_section_when_empty():
    body = _build_text_body(["שם: דן"], "")
    assert "תמלול" not in body


# ── _build_html_body ─────────────────────────────────────────────────────────

def test_html_body_contains_contact_info():
    html = _build_html_body(["שם: דן", "טלפון: 050"], "")
    assert "שם: דן" in html
    assert "טלפון: 050" in html


def test_html_body_includes_transcript_section_when_provided():
    html = _build_html_body(["שם: דן"], "לקוח/ה: שלום")
    assert "תמלול" in html
    assert "שלום" in html


def test_html_body_omits_transcript_section_when_empty():
    html = _build_html_body(["שם: דן"], "")
    assert "תמלול" not in html


def test_html_body_is_rtl():
    html = _build_html_body(["שם: דן"], "")
    assert 'dir="rtl"' in html
    assert "direction:rtl" in html
