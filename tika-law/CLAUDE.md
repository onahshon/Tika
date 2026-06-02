# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

From the `tika-law/` directory (this working directory):

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API (development)
uvicorn backend.app.main:app --reload

# Run the widget test page (separate terminal, then open http://localhost:5173/test.html)
cd frontend && py -m http.server 5173

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

There are no automated tests — no test runner is configured.

## Architecture

This is a single-tenant-per-request SaaS backend serving an embeddable Hebrew chat widget for Israeli employment-law attorneys. The product name is "Tiqa" (AI assistant persona) / "Tika Law" (platform).

**Request flow:**
1. Widget (`frontend/widget.js`) sends messages to `POST /api/v1/chat/message` with `X-Attorney-Id` header.
2. `dependencies.py` extracts and validates the `attorney_id` from the header on every request.
3. `ai_chat.py` maintains in-memory conversation state (keyed by `conversation_id`, 2-hour TTL) and calls `openai_intake.py`.
4. `openai_intake.py` sends the conversation history to OpenAI with a detailed system prompt that enforces JSON-structured responses including `extracted_slots` and `ready_for_attorney`.
5. When `ready_for_attorney=true`, the backend sets `show_contact_form=true` in the response — the widget renders the contact form.
6. On contact form submission (`POST /api/v1/chat/contact`), `notifications.py` sends a Hebrew RTL email with the transcript via Resend.

**Multi-tenancy:** Attorney identity flows through every request via `X-Attorney-Id`. Attorney configs (name, notification email) are stored in `backend/app/core/attorneys.json` — a static file loaded once at startup. There is no database-backed attorney config yet.

**Conversation persistence:** In-memory only (`_CONVERSATIONS` dict in `ai_chat.py`). PostgreSQL models and Alembic migrations are scaffolded but not yet wired to the chat flow.

**AI model:** `gpt-4.1-mini` by default (`OPENAI_MODEL` env var). The system prompt lives in `openai_intake.py` and is the core product logic — it defines triage behavior, slot extraction schema, and Hebrew response style. Do not shorten or restructure it without understanding its triage rules.

**Frontend:** A single vanilla JS widget (`frontend/widget.js`) and `test.html`. The backend serves the frontend as static files at `/widget/*` and exposes `/widget-test` for the test page. No build step — plain JS.

## API Conventions

- Every product endpoint requires `X-Attorney-Id` header (enforced by `require_attorney_id` dependency).
- `attorney_id` in the request body must match the header value.
- `/health` is the only endpoint without `attorney_id`.
- Endpoints are scoped to intake and lead qualification — do not add generic chatbot or CRM infrastructure.

## Attorney Configuration

Add attorneys to `backend/app/core/attorneys.json`:

```json
{
  "attorney-slug": {
    "name": "Attorney Name",
    "email": "attorney@example.com"
  }
}
```

The slug is the `attorney_id` passed by the widget at embed time.

## Environment Variables

See `.env.example`. Key values:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Required for AI responses |
| `OPENAI_MODEL` | Defaults to `gpt-4.1-mini` |
| `RESEND_API_KEY` | Required for attorney email notifications |
| `RESEND_FROM` | Sender address for notifications |
| `DATABASE_URL` | PostgreSQL URL (psycopg driver) |
| `BACKEND_CORS_ORIGINS` | Comma-separated allowed origins |

## Deployment

Deployed on Render. `render.yaml` at the repo root defines the service. Root directory is `tika-law/`, build command is `pip install -r requirements.txt`, start command is `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`. PostgreSQL is not provisioned in the Blueprint — use Supabase or a separate Render database.
