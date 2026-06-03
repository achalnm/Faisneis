import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Faisneis", version="0.1.0")

_origins = ["http://localhost:3000"]
if settings.allowed_origins:
    _origins += [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)[:200]},
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "provider": settings.llm_provider}


class AskRequest(BaseModel):
    question: str


@app.post("/api/ask")
def ask(body: AskRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")

    provider = settings.llm_provider
    if provider == "claude" and not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY is not set. Add it to backend/.env.",
        )
    if provider == "gemini" and not settings.google_api_key:
        raise HTTPException(
            status_code=503,
            detail="GOOGLE_API_KEY is not set. Add it to backend/.env.",
        )

    try:
        from app.agent.pipeline import answer
        result = answer(body.question)
        return result
    except Exception as exc:
        msg = str(exc)
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
            raise HTTPException(status_code=429, detail="AI quota exceeded — try again in a minute.")
        raise HTTPException(status_code=500, detail=msg[:300])


@app.get("/api/debug/speech-search")
def debug_speech_search(q: str, k: int = 5):
    if not q:
        raise HTTPException(status_code=400, detail="q parameter required")
    from app.retrieval.vector_store import query
    results = query(q, k=k)
    return {
        "query": q,
        "results": [
            {
                "text": r["text"][:300],
                "speaker": r["metadata"].get("speaker_name"),
                "date": r["metadata"].get("debate_date"),
                "section": r["metadata"].get("topic_section"),
                "url": r["metadata"].get("source_url"),
                "distance": round(r["distance"], 4),
            }
            for r in results
        ],
    }


@app.get("/api/debug/stats-search")
def debug_stats_search(q: str, k: int = 5):
    if not q:
        raise HTTPException(status_code=400, detail="q parameter required")
    from app.stats.cso_catalog import search_catalog
    results = search_catalog(q, settings.cache_dir, top_k=k)
    return {"query": q, "results": results}
