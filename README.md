# Shrink AI

A RAG-based personal AI therapist with a self-learning episodic memory system.

## Architecture

- **Backend**: FastAPI + Python (SQLAlchemy ORM, Alembic migrations)
- **Frontend**: Next.js
- **LLM**: Gemini 2.0 Flash (primary) / Groq Llama 3.3 70B (fallback)
- **Embeddings**: Gemini text-embedding-004
- **Vector DB**: ChromaDB (local, persistent)
- **Database**: Supabase (PostgreSQL via SQLAlchemy)
- **Auth**: Supabase Auth
- **RAG**: LlamaIndex (Week 2+)

## Quick Start

### 1. Set up environment

```bash
# Root .env (copy and fill in keys)
cp .env.example .env
```

Required keys:
- `GEMINI_API_KEY` — Google AI Studio
- `GROQ_API_KEY` — console.groq.com
- `SUPABASE_URL` + `SUPABASE_ANON_KEY` + `SUPABASE_SERVICE_ROLE_KEY` — Supabase dashboard
- `DATABASE_URL` — Supabase → Settings → Database → Connection string (URI)

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations (creates all tables in Supabase)
alembic upgrade head

# Start the dev server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:3000

### 4. Docker (optional)

```bash
docker-compose up --build
```

## Project Structure

```
shrink-ai/
├── backend/
│   ├── app/
│   │   ├── config.py          # All env settings
│   │   ├── database.py        # SQLAlchemy engine
│   │   ├── supabase_client.py # Auth only
│   │   ├── vector_store.py    # ChromaDB + Gemini embedder
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── routers/           # FastAPI route handlers
│   │   ├── services/          # Business logic
│   │   ├── prompts/           # LLM prompts
│   │   └── middleware/        # Auth middleware
│   ├── alembic/               # DB migrations
│   └── requirements.txt
└── frontend/                  # Next.js app
```

## Phase Build Plan

| Phase | Weeks | Status |
|---|---|---|
| Phase 1+2 (MVP) | 1–6 | 🔨 In Progress |
| Phase 3 (Self-learning deepened) | 7–10 | Planned |
| Phase 4 (Product polish) | 11–14 | Planned |
| Phase 5 (Scale infrastructure) | Post-validation | Planned |
