# Faisneis

An Irish parliamentary Q&A tool. Ask a question in plain English and get a cited answer drawn from Oireachtas debate transcripts and live CSO statistics.

Built as a personal project to make Dail debates more searchable and to cross-reference what politicians say with what the actual numbers show.

**Live:** [faisneis.vercel.app](https://faisneis.vercel.app)

---

## What it does

- Searches Dail and Seanad debates (XML transcripts, 2020 onwards) for relevant speeches
- Pulls live stats from the CSO for economic topics (inflation, rent, unemployment, etc.)
- Routes each question to the right data sources, then writes a cited answer
- Shows a chart when there is time-series data worth plotting
- Every quote and every number links back to its original source

Example questions to try:

- "What did Irish politicians say about housing supply in 2024?"
- "How often has the cost of living been raised in the Dail and what do the inflation figures show?"
- "What has the Minister for Finance said about employment?"

---

## Stack

| Layer | Tech |
| --- | --- |
| Frontend | Next.js, Tailwind CSS, Recharts (Vercel) |
| Backend | FastAPI, Python 3.12 (Render) |
| Vector store | Pinecone serverless |
| Embeddings | fastembed, all-MiniLM-L6-v2 (ONNX, no GPU) |
| LLM | Llama 3.3 70B via Groq |
| Data | Oireachtas Open Data API + CSO PxStat API |

---

## Running locally

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000).

---

## Environment variables

Set these in `backend/.env`:

| Variable | Default | Notes |
| --- | --- | --- |
| `LLM_PROVIDER` | `groq` | `groq`, `gemini`, or `claude` |
| `GROQ_API_KEY` | | Required when using Groq |
| `GOOGLE_API_KEY` | | Required when using Gemini |
| `ANTHROPIC_API_KEY` | | Required when using Claude |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | |
| `PINECONE_API_KEY` | | Pinecone API key |
| `PINECONE_INDEX` | `faisneis-speeches` | Index name |
| `CACHE_DIR` | `./data/cache` | Local cache for API responses |

Frontend needs one variable in `.env.local`:

```env
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
```

---

## Ingesting speeches

Run from `backend/`:

```bash
# test with a single month first
python -m app.ingest.run_ingest --chamber dail --date-start 2024-01-01 --date-end 2024-01-31

# full backfill
python -m app.ingest.run_ingest --chamber both
```

Re-running is safe, it skips speech IDs already in the index.

---

## API endpoints

`POST /api/ask` - main endpoint, streams SSE

```json
{ "question": "What did politicians say about housing supply?" }
```

`GET /api/health` - returns provider name and status

`GET /api/debug/speech-search?q=...` - test semantic search directly

`GET /api/debug/stats-search?q=...` - test CSO catalog matching

---

## Project structure

```text
backend/
  app/
    main.py         FastAPI app and SSE streaming
    config.py       settings via pydantic-settings
    schemas.py      request/response types
    agent/          router, synthesizer, LLM wrappers, pipeline
    retrieval/      Pinecone client and embeddings
    stats/          CSO API client, catalog search, jsonstat parser
    ingest/         Oireachtas XML parser and ingestion scripts
frontend/
  app/              Next.js pages and API client
  components/       AnswerView, SourcesPanel, StatChart
```

---

## Data

Parliamentary debates from the [Houses of the Oireachtas](https://www.oireachtas.ie/en/open-data/) under the Open Data PSI Licence.

Statistics from the [Central Statistics Office](https://www.cso.ie). CSO Ireland.
