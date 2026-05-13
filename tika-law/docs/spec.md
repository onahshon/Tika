# Tika Law MVP Spec

## Purpose

Tika Law helps Israeli employment-law attorneys qualify inbound leads before spending attorney time on review.

## Product Boundary

This product collects intake information and summarizes lead quality. It must not provide legal advice, legal conclusions, or attorney-client relationship language.

## MVP Notes

Placeholder for product flows, lead scoring criteria, Hebrew prompt strategy, data model, and notification rules.

## Conversation Principles

- The assistant should feel like an experienced legal intake coordinator, not a form.
- It should understand the employment-law situation before asking for contact details.
- Early questions should focus on what happened, employment duration, hearing/dismissal stage, employer type, documentation, urgency, and procedural status.
- Contact details should be requested only after the matter appears relevant and worth attorney review.
- Light procedural guidance is allowed when cautious and non-conclusive, such as preserving documents or avoiding signing documents before review.
- The assistant must not provide legal conclusions, determine rights, promise outcomes, or say that the user has a case.

## Orchestration Rules

- The backend owns the intake flow through structured state and slot tracking.
- The LLM must not decide the next required slot on its own.
- Slots include issue, employer, employment duration, current status, procedural stage, documentation, urgency, signed documents, and contact.
- Once a slot is semantically resolved, it must not be asked again.
- Each question slot has a retry limit to prevent loops.
- Contact details are requested only after enough high-signal context exists.
- Most conversations should complete or triage out within 4-7 exchanges.

## Hybrid AI Role

- OpenAI may extract structured slot candidates from natural Hebrew phrasing.
- OpenAI may rewrite the backend-selected next message into concise human wording.
- OpenAI may later summarize conversations for the attorney.
- OpenAI must not choose the next required slot, override stopping conditions, or control lead capture.

## Intent Gate

- Every message is classified before intake advances.
- Greetings receive a natural invitation to describe the work issue.
- Intake questions begin only after minimal employment-law context exists.
- Unclear or unrelated openers do not advance the flow.
- Active-question answers are interpreted in the context of the current slot.
