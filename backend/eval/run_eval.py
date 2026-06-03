"""
Evaluation harness for the golden question set.

Checks:
  1. Every [S1]/[C1] marker in the answer has a matching citation.
  2. "honest_no_data" questions get confidence=low or medium and a non-empty caveat.
  3. For stat citations, the value in the citation is a real number (basic sanity,
     not a hallucinated value like "1000%" on a typical CPI series).

Run from backend/ after setting LLM_PROVIDER and API key:
    python eval/run_eval.py

Requires the vector store to have data loaded (run run_ingest.py first).
"""

import json
import re
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent.pipeline import answer as run_pipeline
from app.config import settings

GOLDEN_PATH = Path(__file__).parent / "golden.jsonl"


def load_golden():
    with open(GOLDEN_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]


def check_citation_completeness(answer_text: str, speech_cits, stat_cits) -> tuple[bool, str]:
    """Every [SN] / [CN] marker in the prose must have a matching citation entry."""
    markers = set(re.findall(r"\[([SC]\d+)\]", answer_text))
    present_refs = {c.ref for c in speech_cits} | {c.ref for c in stat_cits}
    missing = markers - present_refs
    if missing:
        return False, f"Markers {sorted(missing)} appear in answer but have no citation"
    return True, "ok"


def check_honest_no_data(result) -> tuple[bool, str]:
    """When the data genuinely cannot answer, confidence should not be high and caveats should be set."""
    ans = result.answer
    if ans.confidence == "high":
        return False, f"Expected low/medium confidence for unanswerable question, got high"
    if not ans.caveats.strip():
        return False, "Expected a non-empty caveat for unanswerable question"
    return True, "ok"


def check_stat_values(stat_cits, stats_topics) -> tuple[bool, str]:
    """Basic sanity: stat citations should contain a number, not obviously absurd values."""
    for c in stat_cits:
        val_str = c.value_or_range.strip()
        # Extract any number from the string
        nums = re.findall(r"-?\d+\.?\d*", val_str)
        if not nums:
            return False, f"Stat citation {c.ref} has no numeric value: {val_str!r}"
        # Basic range check: for CPI / unemployment / completion values
        # they should be between -100 and 100,000
        val = float(nums[0])
        if val < -100 or val > 100000:
            return False, f"Stat citation {c.ref} has implausible value {val}"
    return True, "ok"


def run():
    cases = load_golden()
    print(f"Running {len(cases)} evaluation cases\n")

    rows = []
    for case in cases:
        qid = case["id"]
        question = case["question"]
        print(f"  [{qid}] {question[:60]}...")

        try:
            result = run_pipeline(question)
        except Exception as e:
            rows.append({"id": qid, "pass": False, "reason": f"Exception: {e}"})
            traceback.print_exc()
            continue

        fails = []
        ans = result.answer

        # Check 1: citation completeness
        ok, msg = check_citation_completeness(
            ans.answer, ans.speech_citations, ans.stat_citations
        )
        if not ok:
            fails.append(msg)

        # Check 2: honest no-data cases
        if case.get("honest_no_data"):
            ok, msg = check_honest_no_data(result)
            if not ok:
                fails.append(msg)

        # Check 3: stat citation values are numeric and plausible
        if ans.stat_citations:
            ok, msg = check_stat_values(ans.stat_citations, case.get("stats_topics", []))
            if not ok:
                fails.append(msg)

        # Check 4: answer is non-empty
        if not ans.answer.strip():
            fails.append("Answer is empty")

        passed = len(fails) == 0
        rows.append({"id": qid, "pass": passed, "reason": "; ".join(fails) if fails else "ok"})
        status = "PASS" if passed else "FAIL"
        print(f"    {status} — {rows[-1]['reason']}")

    total = len(rows)
    passed = sum(1 for r in rows if r["pass"])
    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} passed")
    print(f"{'=' * 60}")

    print(f"\n{'ID':<35} {'Result':<6} Reason")
    print("-" * 80)
    for r in rows:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"{r['id']:<35} {status:<6} {r['reason']}")

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    if not settings.anthropic_api_key and not settings.google_api_key:
        print("No API key set. Add ANTHROPIC_API_KEY or GOOGLE_API_KEY to backend/.env")
        sys.exit(1)
    run()
