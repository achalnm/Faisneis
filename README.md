# Fáisnéis

A question-answering system that cross-references Irish parliamentary debates with
official economic statistics from the Central Statistics Office. Ask a question in
plain English and get a grounded, cited answer drawn from Oireachtas transcripts and
live CSO data.

Every number and every quote traces to an openable source.

**Live:** [faisneis.vercel.app](https://faisneis.vercel.app)

---

## What it does

- Searches Dáil and Seanad debates (Akoma Ntoso XML, 2020 onwards) for relevant speeches
- Fetches live CSO statistics for economic topics (inflation, employment, housing, etc.)
- Routes questions to the right tools, retrieves evidence, and synthesises a cited answer
- Shows the router's reasoning so you can see why it answered the way it did
- Renders a time-series chart when statistical data is available

Example questions:

- "What did Irish politicians say about housing supply in 2024?"
- "How often has the cost of living been raised in the Dáil this year, and what do the inflation figures show?"
- "What has the Minister for Finance said about employment, and how does that compare to the CSO unemployment rate?"

---

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js, Tailwind CSS, Recharts — deployed on Vercel |
| Backend | FastAPI, Python 3.11 — deployed on Render |
| Vector store | Pinecone (serverless) |
| Embeddings | fastembed / ONNX (all-MiniLM-L6-v2, no GPU needed) |
| LLM | Gemini 2.5 Flash or Claude (configurable) |
| Data | Oireachtas API + CSO PxStat API |

---

## Local setup

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Configuration

All settings live in `backend/.env`:

| Variable | Default | Notes |
| --- | --- | --- |
| `LLM_PROVIDER` | `gemini` | `gemini` or `claude` |
| `GOOGLE_API_KEY` | | Required when using Gemini |
| `ANTHROPIC_API_KEY` | | Required when using Claude |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Optional model override |
| `PINECONE_API_KEY` | | Required for cloud vector store |
| `PINECONE_INDEX` | `faisneis-speeches` | Pinecone index name |
| `INGEST_DATE_START` | `2020-01-01` | Start of ingestion window |
| `INGEST_DATE_END` | today | End of ingestion window |
| `CACHE_DIR` | `./data/cache` | Disk cache for API responses |

---

## Ingestion

Run from `backend/` to populate the vector store:

```bash
# Dry run first to check what would be added
python -m app.ingest.run_ingest --dry-run

# Single month (fast, good for testing)
python -m app.ingest.run_ingest --chamber dail --date-start 2024-01-01 --date-end 2024-01-31

# Full window, both chambers
python -m app.ingest.run_ingest --chamber both
```

Ingestion is idempotent — re-running skips already-loaded speech IDs. API responses
are cached to `CACHE_DIR` so re-runs are fast.

---

## API

### `POST /api/ask`

```json
{ "question": "What did politicians say about housing supply?" }
```

Returns `tool_plan`, `answer` (with citations), and optional `chart_data`.

### `GET /api/health`

Returns `{ "status": "ok", "provider": "gemini" }`.

### `GET /api/debug/speech-search?q=...`

Runs a semantic search and returns the top matching speech chunks.

### `GET /api/debug/stats-search?q=...`

Searches the CSO catalog and returns candidate matrix codes.

---

## Evaluation

```bash
cd backend
python eval/run_eval.py
```

Runs the golden question set and checks citation completeness, confidence calibration,
and numeric plausibility of stat citations.

---

## Project layout

```text
faisneis/
  backend/
    app/
      main.py           FastAPI routes
      config.py         Settings from .env
      schemas.py        Pydantic models
      ingest/           Oireachtas client, AKN parser, chunker, ingest CLI
      retrieval/        Pinecone/Chroma vector store and embeddings
      stats/            CSO client, catalog search, JSON-stat parser
      agent/            LLM abstraction, router, synthesizer, pipeline
    eval/               Golden question set and eval harness
    scripts/            Migration and verification utilities
  frontend/
    app/                Next.js App Router pages and API client
    components/         AnswerView, SourcesPanel, StatChart
```

---

## Data sources

Parliamentary debates published by the Houses of the Oireachtas under the
[Open Data PSI Licence](https://www.oireachtas.ie/en/open-data/).

Statistics published by the Central Statistics Office.
© Central Statistics Office, Ireland. [cso.ie](https://www.cso.ie)
