# uv run python -m research_learning_agent.scripts.intent_regression --print-mismatches

from __future__ import annotations


import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from research_learning_agent.intent_classifier import IntentClassifier
from research_learning_agent.schemas import UserProfile, UserLevel


DEFAULT_CASES_PATH = Path("tests/fixtures/intent_cases.json")
DEFAULT_OUT_DIR = Path("tests/results/intent_regression_runs")


@dataclass
class Case:
    id: str
    query: str
    expected_intent: str
    note: str | None = None


def _load_cases(path: Path) -> list[Case]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[Case] = []
    for item in data:
        out.append(
            Case(
                id=str(item["id"]),
                query=str(item["query"]),
                expected_intent=str(item["expected_intent"]),
                note=str(item.get("note", None)),
            )
        )
    return out


def _now_run_id() -> str:
    # sortable run id
    return time.strftime("%Y%m%d_%H%M%S")


def _safe_env_profile() -> UserProfile:
    """
    Regression harness should not overweight profile.
    Use a minimal, stable profile across runs.
    """
    level = os.getenv("INTENT_TEST_LEVEL", UserLevel.beginner).strip() or UserLevel.beginner
    # If UserProfile has more fields, keep them minimal/empty
    return UserProfile(user_id="test_user", background="", level=level, goals="")


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    correct = sum(1 for r in rows if r["predicted_intent"] == r["expected_intent"])
    acc = (correct / total) if total else 0.0
    use_llm = sum(1 for r in rows if r["use_llm"])
    use_llm_rate = (use_llm / total) if total else 0.0

    by_expected: dict[str, dict[str, int]] = {}
    ask_count = 0
    avg_conf = 0.0

    for r in rows:
        exp = r["expected_intent"]
        pred = r["predicted_intent"]
        by_expected.setdefault(exp, {})
        by_expected[exp][pred] = by_expected[exp].get(pred, 0) + 1
        if r.get("should_ask_clarifying_question"):
            ask_count += 1
        avg_conf += float(r.get("confidence", 0.0))

    avg_conf = (avg_conf / total) if total else 0.0

    return {
        "total": total,
        "correct": correct,
        "accuracy": round(acc, 4),
        "clarify_rate": round((ask_count / total) if total else 0.0, 4),
        "avg_confidence": round(avg_conf, 4),
        "use_llm_rate": round(use_llm_rate, 4),
        "confusion_by_expected": by_expected,
    }


def _print_summary(summary: dict[str, Any]) -> None:
    print("\n=== Intent Regression Summary ===")
    print(f"Total cases:     {summary['total']}")
    print(f"Correct:         {summary['correct']}")
    print(f"Accuracy:        {summary['accuracy']:.2%}")
    print(f"Clarify Rate:    {summary['clarify_rate']:.2%}")
    print(f"Avg Confidence:  {summary['avg_confidence']:.3f}")
    print(f"LLM Use Rate:    {summary['use_llm_rate']:.2%}")

    print("\nConfusion by expected intent:")
    for exp, preds in summary["confusion_by_expected"].items():
        preds_str = ", ".join([f"{p}={n}" for p, n in sorted(preds.items(), key=lambda x: -x[1])])
        print(f"  - {exp}: {preds_str}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Intent regression harness (heuristics + optional LLM fallback)")
    ap.add_argument("--cases", type=str, default=str(DEFAULT_CASES_PATH), help="Path to intent cases JSON file")
    ap.add_argument("--out_dir", type=str, default=str(DEFAULT_OUT_DIR), help="Output directory for results")
    ap.add_argument("--max-cases", type=int, default=0, help="Max cases to run (0=all)")
    ap.add_argument("--min-accuracy", type=float, default=0.80, help="Fail if accuracy below this threshold")
    ap.add_argument("--print-mismatches", action="store_true", help="Print mismatched cases")
    args = ap.parse_args(argv)

    cases_path = Path(args.cases)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = _now_run_id()
    out_jsonl = out_dir / f"intent_run_{run_id}.jsonl"
    out_summary = out_dir / f"intent_run_{run_id}_summary.json"

    cases = _load_cases(cases_path)
    if args.max_cases and args.max_cases > 0 and args.max_cases < len(cases):
        cases = cases[:args.max_cases]
    
    profile = _safe_env_profile()

    clf = IntentClassifier()

    rows: list[dict[str, Any]] = []

    for c in cases:
        res = clf.classify(c.query, profile)
        row = {
            "id": c.id,
            "query": c.query,
            "expected_intent": c.expected_intent,
            "predicted_intent": getattr(res, "intent", None),
            "confidence": getattr(res, "confidence", None),
            "use_llm": getattr(res, "use_llm", None),
            "should_ask_clarifying_question": getattr(res, "should_ask_clarifying_question", None),
            "clarifying_question": getattr(res, "clarifying_question", None),
            "reasoning": getattr(res, "reasoning", None),
            "suggested_output": getattr(res, "suggested_output", None),
            "note": c.note,
        }
        rows.append(row)

        with out_jsonl.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        
    summary = _summarize(rows)
    out_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    _print_summary(summary)

    if args.print_mismatches:
        mismatches = [r for r in rows if r["predicted_intent"] != r["expected_intent"]]
        if mismatches:
            print("\n=== Mismatched Cases ===")
            for r in mismatches:
                print(f"- {r['id']} expected={r['expected_intent']} got={r['predicted_intent']} conf={r['confidence']}")
                print(f"  query: {r['query']}")
                if r.get("should_ask_clarifying_question"):
                    print(f"    clarify?: {r['clarifying_question']}")
                if r.get("rationale"):
                    print(f"    rationale: {r['rationale']}")
        else:
            print("\nAll cases matched!")
    
    # Exit code for CI usage
    ok = summary["accuracy"] >= args.min_accuracy
    return 0 if ok else 2  # exit code 2 means regression failure


if __name__ == "__main__":
    raise SystemExit(main())