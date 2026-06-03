"""
Quick smoke test for the LLM provider abstraction.

Run after adding your API key to backend/.env:
    LLM_PROVIDER=claude
    ANTHROPIC_API_KEY=sk-ant-...

or:
    LLM_PROVIDER=gemini
    GOOGLE_API_KEY=AIza...

Then:
    python scripts/verify_llm.py
"""

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
    # Clear lru_cache so the new provider is picked up
    get_llm.cache_clear()
    try:
        llm = get_llm()
        text = llm.complete(SYSTEM, USER)
        print(f"complete(): {text.strip()}")
        obj = llm.complete_json(JSON_SYSTEM, JSON_USER)
        print(f"complete_json(): {obj}")
    except Exception as e:
        print(f"ERROR: {e}")

if settings.anthropic_api_key:
    test_provider("claude")
else:
    print("Skipping claude: ANTHROPIC_API_KEY not set")

if settings.google_api_key:
    test_provider("gemini")
else:
    print("Skipping gemini: GOOGLE_API_KEY not set")

if not settings.anthropic_api_key and not settings.google_api_key:
    print("\nNo API keys found. Add one to backend/.env and re-run.")
    sys.exit(1)
