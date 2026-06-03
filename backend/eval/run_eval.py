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
    markers = set(re.findall(r"\[([SC]\d+)\]", answer_text))
    present_refs = {c.ref for c in speech_cits} | {c.ref for c in stat_cits}
    missing = markers - present_refs
    if missing:
        return False, f"Markers {sorted(missing)} appear in answer but have no citation"
    return True, "ok"


def check_honest_no_data(result) -> tuple[bool, str]:
    ans = result.answer
    if ans.confidence == "high":
        return False, "Expected low/medium confidence for unanswerable question, got high"
    if not ans.caveats.strip():
        return False, "Expected a non-empty caveat for unanswerable question"
    return True, "ok"


def check_stat_values(stat_cits, stats_topics) -> tuple[bool, str]:
    for c in stat_cits:
        val_str = c.value_or_range.strip()
        nums = re.findall(r"-?\d+\.?\d*", val_str)
        if not nums:
            return False, f"Stat citation {c.ref} has no numeric value: {val_str!r}"
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

        ok, msg = check_citation_completeness(ans.answer, ans.speech_citations, ans.stat_citations)
        if not ok:
            fails.append(msg)

        if case.get("honest_no_data"):
            ok, msg = check_honest_no_data(result)
            if not ok:
                fails.append(msg)

        if ans.stat_citations:
            ok, msg = check_stat_values(ans.stat_citations, case.get("stats_topics", []))
            if not ok:
                fails.append(msg)

        if not ans.answer.strip():
            fails.append("Answer is empty")

        passed = len(fails) == 0
        rows.append({"id": qid, "pass": passed, "reason": "; ".join(fails) if fails else "ok"})
        print(f"    {'PASS' if passed else 'FAIL'} - {rows[-1]['reason']}")

    total = len(rows)
    passed = sum(1 for r in rows if r["pass"])
    print(f"\nResults: {passed}/{total} passed\n")
    print(f"{'ID':<35} {'Result':<6} Reason")
    print("-" * 80)
    for r in rows:
        print(f"{r['id']:<35} {'PASS' if r['pass'] else 'FAIL':<6} {r['reason']}")

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    if not settings.anthropic_api_key and not settings.google_api_key:
        print("No API key set. Add ANTHROPIC_API_KEY or GOOGLE_API_KEY to backend/.env")
        sys.exit(1)
    run()
