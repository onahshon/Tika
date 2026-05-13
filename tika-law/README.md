# Tika Law

Tika Law is an AI-powered lead qualification MVP for Israeli employment-law attorneys.

It is designed to collect structured intake information, ask focused follow-up questions, score and classify lead quality, notify the attorney, and save conversations.

This is not a legal advice system.

## Stack

- Backend: Python 3.12, FastAPI
- Database: PostgreSQL, Supabase compatible
- ORM/migrations: SQLAlchemy, Alembic
- Frontend: embeddable JavaScript widget
- Hosting target: Render
- AI: OpenAI API
- Language: Hebrew-first

## Project Structure

```text
tika-law/
  backend/
    app/
      api/
      core/
      db/
      models/
      prompts/
      services/
      main.py
    alembic/
  frontend/
  docs/
```

## Development Setup

From this folder:

```powershell
cd tika-law
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Update `.env` with your local or Supabase PostgreSQL connection string and OpenAI API key.

Run the API:

```powershell
uvicorn backend.app.main:app --reload
```

Health check:

```text
GET http://localhost:8000/health
```

Widget test page:

```powershell
cd frontend
py -m http.server 5173
```

Open `http://localhost:5173/test.html`, set the API URL to `http://localhost:8000`, and click the health check button.

When deployed on Render, open:

```text
https://YOUR_RENDER_SERVICE_URL/widget-test
```

## Render Deployment

This repo includes a root-level `render.yaml` Blueprint for the backend service.

In Render:

1. Create a new Blueprint.
2. Connect the GitHub repo.
3. Use the default Blueprint path: `render.yaml`.
4. Fill the secret environment values when prompted, especially `OPENAI_API_KEY` and `BACKEND_CORS_ORIGINS`.

PostgreSQL is intentionally not provisioned by the current Blueprint because Render allows only one active free-tier database per account. Add `DATABASE_URL` later using Supabase or a paid Render PostgreSQL instance before implementing persistence.

The backend service uses:

```text
Root directory: tika-law
Build command: pip install -r requirements.txt
Start command: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
Health check: /health
```

## Database

The backend expects `DATABASE_URL` to be a PostgreSQL-compatible SQLAlchemy URL.

Example:

```text
postgresql+psycopg://postgres:postgres@localhost:5432/tika_law
```

Run migrations after models are added:

```powershell
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

## API Conventions

- Product APIs must include `attorney_id` on every request.
- Prefer `X-Attorney-Id` for API requests from the embeddable widget or server integrations.
- The `/health` endpoint is operational and does not require `attorney_id`.
- Keep endpoints specific to intake and lead qualification. Do not add generic chatbot infrastructure.

## MVP Scope

Included later:

- Structured lead intake
- Hebrew-first follow-up questions
- Lead quality scoring
- Lead classification
- Attorney notification
- Conversation persistence

Out of scope for now:

- Legal advice
- Billing
- CRM
- Analytics dashboard
- WhatsApp integration
