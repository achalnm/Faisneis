import asyncio
import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
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


@app.get("/api/health")
def health():
    return {"status": "ok", "provider": settings.llm_provider}


class AskRequest(BaseModel):
    question: str


@app.post("/api/ask")
async def ask(body: AskRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")

    provider = settings.llm_provider
    if provider == "claude" and not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY is not set.")
    if provider == "gemini" and not settings.google_api_key:
        raise HTTPException(status_code=503, detail="GOOGLE_API_KEY is not set.")

    async def stream():
        # Send SSE heartbeat comments every 5 seconds to prevent proxy/Render timeouts.
        # The final event is a "result" with the JSON payload.
        loop = asyncio.get_event_loop()
        done = asyncio.Event()
        result_box = {}

        def run_pipeline():
            try:
                from app.agent.pipeline import answer
                result_box["ok"] = answer(body.question)
            except Exception as exc:
                result_box["err"] = str(exc)
            finally:
                loop.call_soon_threadsafe(done.set)

        import threading
        threading.Thread(target=run_pipeline, daemon=True).start()

        while not done.is_set():
            yield ": heartbeat\n\n"
            try:
                await asyncio.wait_for(asyncio.shield(done.wait()), timeout=5)
            except asyncio.TimeoutError:
                pass

        if "ok" in result_box:
            try:
                payload = result_box["ok"].model_dump()
                # Coerce numpy/non-standard floats that json.dumps can't handle
                data_str = json.dumps(payload, default=lambda x: float(x) if hasattr(x, '__float__') else str(x))
            except Exception as e:
                logger.error("Serialization error: %s", e)
                yield f"event: error\ndata: {json.dumps({'detail': f'Serialization error: {e}'})}\n\n"
                return
            yield f"event: result\ndata: {data_str}\n\n"
        else:
            msg = result_box.get("err", "Unknown error")
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                detail = "AI quota exceeded — try again in a minute."
            elif "503" in msg or "UNAVAILABLE" in msg:
                detail = "AI model temporarily overloaded — try again in a moment."
            else:
                detail = msg[:300]
            yield f"event: error\ndata: {json.dumps({'detail': detail})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


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
