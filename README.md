# Faisneis

Ask a question about Irish politics or economics and get a cited answer drawn from Dail and Seanad debate transcripts, cross-referenced with live CSO statistics.

Built as a personal project. Wanted a way to search what politicians actually said on a topic and compare it to what the numbers show.

**Live:** [faisneis.vercel.app](https://faisneis.vercel.app)

---

## What it does

Each question goes through a two-step pipeline. First the LLM decides whether the question needs speech search, stat lookup, or both. Then it fetches the relevant data and writes a cited answer grounded only in what the sources actually say.

Speech citations link back to the original Oireachtas debate page. Stat citations link to the CSO PxStat table. If there is a time series worth showing, a chart gets drawn alongside the answer.

The backend also handles greetings, thanks, and short nonsense without hitting the LLM at all.

---

## Screenshots

### Asking about housing supply

![Housing supply question](Screenshots/q-housing-supply.png)

Heather Humphreys and Michael McGrath both cited on the same question. Each [S1], [S2] marker is a clickable link back to the original Oireachtas debate.

### Rent trends

![Rent question](Screenshots/q-rent-trends.png)

The router decided this needed both speech search and stats. Pulled the Residential Property Price Index from CSO alongside the debate quotes.

### Immigration debates

![Immigration question](Screenshots/q-immigration.png)

Multiple TDs cited from different sessions and dates on the same topic. Citations are pinned to the exact speech, not just the debate.

### Cost of living

![Cost of living question](Screenshots/q-cost-of-living.png)

Cross-party coverage on the same question from different dates and sessions.

### International students

![International students question](Screenshots/q-international-students.png)

A narrower topic that still finds relevant speeches. The search is semantic so it catches debates where the exact phrase was not used.

### CSO chart alongside the answer

![Unemployment with chart](Screenshots/q-unemployment-chart.png)

When a question has a statistical angle the app fetches live CSO data and draws a chart next to the answer. This one pulled the monthly Live Register series.

---

## Stack

| Layer | Tech |
| --- | --- |
| Frontend | Next.js 16, Tailwind CSS v4, Recharts (Vercel) |
| Backend | FastAPI, Python 3.12 (Render free tier) |
| Vector store | Pinecone serverless (384-dim cosine, us-east-1) |
| Embeddings | fastembed all-MiniLM-L6-v2 (ONNX, no GPU) |
| LLM | Llama 3.3 70B via Groq (Gemini 2.5 Flash fallback if GOOGLE_API_KEY is set) |
| Stats | CSO PxStat REST API (live, no auth needed) |
| Data | Oireachtas Open Data API (Dail and Seanad XML transcripts, 2020 onwards) |

---

## Running locally

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# fill in GROQ_API_KEY and PINECONE_API_KEY
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
# create .env.local with:
# NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000).

---

## Environment variables

Set these in `backend/.env`:

| Variable | Default | Notes |
| --- | --- | --- |
| `LLM_PROVIDER` | `groq` | `groq` or `gemini` |
| `GROQ_API_KEY` | | Required when using Groq |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | |
| `GOOGLE_API_KEY` | | Required for Gemini or as Groq fallback |
| `GEMINI_MODEL` | `gemini-2.5-flash` | |
| `PINECONE_API_KEY` | | Required |
| `PINECONE_INDEX` | `faisneis-speeches` | |
| `CACHE_DIR` | `./data/cache` | CSO responses cached to disk here |

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

Re-running is safe, existing IDs get looked up first so nothing gets duplicated.

---

## API

`POST /api/ask` streams SSE

```json
{ "question": "What did politicians say about housing supply?" }
```

The response is a server-sent event stream. Two event types: `result` (the full JSON payload) and `error`. Repeated identical questions are served from an in-memory cache with a 2 hour TTL.

`GET /api/health` returns the active LLM provider

`GET /api/debug/speech-search?q=...` tests semantic search directly

`GET /api/debug/stats-search?q=...` tests CSO catalog matching

---

## Project structure

```text
backend/
  app/
    main.py         FastAPI app, SSE streaming, response cache
    config.py       settings via pydantic-settings
    schemas.py      request and response types
    agent/          router, synthesizer, LLM wrappers, pipeline
    retrieval/      Pinecone and Chroma clients, fastembed wrapper
    stats/          CSO API client, catalog keyword search, jsonstat parser
    ingest/         Oireachtas XML parser and ingestion scripts
frontend/
  app/              Next.js pages and API client
  components/       Masthead, QuestionDesk, AnswerView, SourcesPanel, StatChart
```

---

## Infrastructure

### Pinecone

![Pinecone index](Screenshots/pinecone-index.png)

315,300 speech chunks. Each record stores speaker name, debate date, chamber, and the direct URL back to the Oireachtas website.

### Render

![Render backend](Screenshots/render-backend.png)

FastAPI on Render free tier. The ONNX embedding model gets pre-baked at build time so cold starts do not trigger a model download. Still takes 10-15 seconds to wake after idle.

### Vercel

![Vercel frontend](Screenshots/vercel-frontend.png)

Next.js frontend on Vercel. Builds in about 30 seconds.

---

## Things that did not work

**Hosting.** Railway needs a paid plan for persistent volumes. Oracle Cloud signup kept failing. Fly.io free tier is basically gone. Koyeb showed 30 USD/month upfront. Ended up on Render which is genuinely free with no card required, but the 512MB RAM limit caused its own problems.

**sentence-transformers killed the server.** First embedding setup used sentence-transformers with PyTorch. Crashed on Render after a few seconds with OOM. PyTorch alone is 400MB. Switched to fastembed which uses ONNX runtime and brought memory down to a workable level.

**The CSO catalog search was slow.** Originally embedded all 12,000+ CSO table titles at startup to find relevant stats. On Render this took over 2 minutes on cold start. Replaced with simple keyword matching which runs in under 0.1 seconds and is just as accurate for this use case.

**Render 30 second timeout.** Some answers were taking 40-50 seconds. Render kills any request that does not start responding within 30 seconds. Fixed by switching to SSE and sending heartbeat comments every few seconds while the answer generates.

**SSE parser bug.** The frontend was randomly getting "stream ended without a result" errors. The `eventType` and `dataLine` variables were being declared inside the while loop and reset on every iteration. When an event and its data arrived in different network chunks the parser lost the event type. Moving the declarations outside the loop fixed it.

**Gemini free tier rate limit.** Gemini 2.5 Flash free tier allows 10 requests per minute. Fine for normal use but hits the limit immediately in any kind of batch. Switched to Groq as the primary provider which gives 30 RPM and 14,400 requests per day on the free tier.

**Speaker name detection.** Querying "what did the Minister for Finance say" was returning nothing because the code was filtering Pinecone by `speaker_name = "Minister for Finance"` which matched nobody. Added logic to detect when a speaker string is a role title rather than a person name, and skip the filter in that case.

**Date filtering.** Range queries on string-formatted dates via Pinecone metadata filters were returning unexpected results. Moved date filtering to Python after fetching a wider result set.

---

## Data

Parliamentary debates from the [Houses of the Oireachtas](https://www.oireachtas.ie/en/open-data/) under the Open Data PSI Licence.

Statistics from [CSO Ireland](https://www.cso.ie) via the PxStat API, open data.
