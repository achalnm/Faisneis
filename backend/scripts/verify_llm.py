import sys
sys.path.insert(0, ".")

from app.config import settings
from app.agent.llm import get_llm

SYSTEM = "You are a concise assistant. Respond in one sentence."
USER = "What is the capital of Ireland?"
JSON_SYSTEM = "Answer the question as JSON only."
JSON_USER = 'What is the capital of Ireland? Return {"capital": "...", "country": "..."}'


def test_provider(provider: str):
    print(f"\n--- Testing {provider} ---")
    settings.__dict__["llm_provider"] = provider
    get_llm.cache_clear()
    try:
        llm = get_llm()
        text = llm.complete(SYSTEM, USER)
        print(f"complete(): {text.strip()}")
        obj = llm.complete_json(JSON_SYSTEM, JSON_USER)
        print(f"complete_json(): {obj}")
    except Exception as e:
        print(f"ERROR: {e}")


if settings.groq_api_key:
    test_provider("groq")
else:
    print("Skipping groq: GROQ_API_KEY not set")

if settings.google_api_key:
    test_provider("gemini")
else:
    print("Skipping gemini: GOOGLE_API_KEY not set")

if not settings.groq_api_key and not settings.google_api_key:
    print("No API keys found. Add GROQ_API_KEY or GOOGLE_API_KEY to backend/.env and re-run.")
    sys.exit(1)
