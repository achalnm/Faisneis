# Fáisnéis

A question-answering system that cross-references Irish parliamentary debates with
official economic statistics from the Central Statistics Office. Ask a question in
plain English and get a grounded, cited answer drawn from Oireachtas transcripts and
live CSO data.

Every number and every quote traces to an openable source. A narrow tool that never
lies is the goal.

---

## What it does

- Searches Dáil and Seanad debates (Akoma Ntoso XML, 2020 onwards) for relevant speeches
- Fetches live CSO statistics for economic topics (inflation, employment, housing, etc.)
- Routes questions to the right tools, retrieves evidence, and synthesises a cited answer
- Shows the router's reasoning so you can see why it answered the way it did
- Renders a time-series chart when statistical data is present

Example questions it handles well:

- "What did Irish politicians say about housing supply in 2024, and did the CSO data support their claims?"
- "How often has the cost of living been raised in the Dáil this year, and what do the inflation figures actually show?"
- "What has the Minister for Finance said about employment, and how does that compare to the CSO unemployment rate?"

---

## Requirements

- Python 3.11+
- Node.js 18+
- An API key for either Anthropic (Claude) or Google (Gemini)

---

## Setup

### Backend

```bash
cd backend
pip install fastapi uvicorn[standard] httpx lxml pandas pydantic pydantic-settings \
    sentence-transformers chromadb python-dotenv anthropic google-generativeai
```

Copy the example env file and fill in your key:

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY or GOOGLE_API_KEY
```

### Frontend

```bash
cd frontend
npm install
```

---

## Configuration

All settings live in `backend/.env`. The main ones:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `claude` | Which LLM to use. Set to `claude` or `gemini`. |
| `ANTHROPIC_API_KEY` | | Required when `LLM_PROVIDER=claude`. Note: this is the API key from console.anthropic.com, not a Claude.ai Pro subscription. |
| `GOOGLE_API_KEY` | | Required when `LLM_PROVIDER=gemini`. |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Optional model override. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Optional model override. |
| `EMBED_MODEL` | `all-MiniLM-L6-v2` | Local embedding model. Swap to `BAAI/bge-small-en-v1.5` for better quality. |
| `INGEST_DATE_START` | `2020-01-01` | Start of the ingestion window. |
| `INGEST_DATE_END` | today | End of the ingestion window. Leave blank for today. |
| `CHROMA_DIR` | `./data/chroma` | Where the vector store lives on disk. |
| `CACHE_DIR` | `./data/cache` | Raw API response cache. Re-runs never re-fetch. |

To switch from Claude to Gemini, update `.env`:

```
LLM_PROVIDER=gemini
GOOGLE_API_KEY=AIza...
```

No code changes needed.

---

## Running ingestion

Run from `backend/`:

```bash
# Single month (good first run to verify quality)
python -m app.ingest.run_ingest --chamber dail --date-start 2024-01-01 --date-end 2024-01-31

# Full window, both chambers
python -m app.ingest.run_ingest --chamber both

# Dry run to see what would be added
python -m app.ingest.run_ingest --dry-run
```

The ingest is idempotent. Re-running skips already-loaded speech IDs. Raw JSON and
XML responses are cached in `CACHE_DIR` so re-runs are fast even if they need to
re-parse.

Embedding is done locally with sentence-transformers (no API cost). The first run
downloads the model (~80 MB) from HuggingFace.

---

## Running the app

Terminal 1 (backend):

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Terminal 2 (frontend):

```bash
cd frontend
npm run dev
```

Open http://localhost:3000.

---

## API

### POST /api/ask

```json
{ "question": "What did politicians say about housing supply?" }
```

Returns an `AskResponse` with `tool_plan`, `answer`, and optional `chart_data`.

### GET /api/debug/speech-search?q=...

Runs a semantic search over the Chroma store and returns the top matches. Good for
checking ingestion quality.

### GET /api/debug/stats-search?q=...

Searches the CSO catalog by topic and returns candidate matrix codes.

### GET /api/health

Returns `{ "status": "ok", "provider": "claude" }`.

---

## Evaluation

```bash
cd backend
python eval/run_eval.py
```

Runs 10 golden questions and checks:

1. Every citation marker in the answer has a matching citation object.
2. "Unanswerable" questions get low or medium confidence with an honest caveat.
3. Stat citation values are numeric and within a plausible range.

---

## Data sources and attribution

Parliamentary debates are published by the Houses of the Oireachtas under the
Open Data PSI Licence. Source: [oireachtas.ie](https://www.oireachtas.ie).

Statistics are published by the Central Statistics Office.
Copyright Central Statistics Office, Ireland. Source: [cso.ie](https://www.cso.ie).

---

## Project layout

```
faisneis/
  backend/
    app/
      main.py           FastAPI routes
      config.py         Settings from .env
      schemas.py        Pydantic models
      ingest/           Oireachtas client, AKN parser, chunker, ingest CLI
      retrieval/        Chroma wrapper and embeddings
      stats/            CSO client, catalog search, JSON-stat parser
      agent/            LLM abstraction, router, synthesizer, pipeline
    eval/               Golden question set and eval harness
    scripts/            Smoke test, LLM verification script
  frontend/
    app/                Next.js App Router pages and API client
    components/         AnswerView, SourcesPanel, StatChart
```
