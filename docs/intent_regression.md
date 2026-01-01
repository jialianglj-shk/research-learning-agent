# Intent Regression Harness

This project includes a small regression harness to track the **intent classifier** behavior over time.\
It automates what would otherwise be a manual process:

> run a fixed set of canned queries → record predictions → compare to expected → review mismatches

The harness **supports LLM fallback** and records whether the classifier asks
a clarifying question.

---

## Why this exists

Intent classification is a critical control signal for:
- Learning mode selection (Day 5+)
- Planning strategy and tool usage
- When to ask clarifying questions

LLM-only intent classification tends to drift or collapse (e.g., overproducing `guided_study`).\
This harness makes intent changes **observable**, **measurable**, and **repeatable**.

---

## Test Cases

Canned queries live in:

- `tests/fixtures/intent_cases.json` (default)

Each case includes:
- `id`: stable identifier
- `query`: the user message
- `expected_intent`: one of:
  - `casual_curiosity`
  - `guided_study`
  - `professional_research`
  - `urgent_troubleshooting`
- optional `note`: for ambiguous cases, special expectations, etc.

Example:

```json
{
  "id": "c01",
  "query": "What is reinforcement learning?",
  "expected_intent": "casual_curiosity",
  "note": "Simple definition question; should not default to guided_study"
}

## Running the Harness

Run:
```bash
uv run python -m research_learning_agent.scripts.intent_regression --print-mismatches
```

Useful flags:
- `--cases PATH`: custom cases file (default: `tests/fixtures/intent_cases.json`)
- `--out-dir PATH`: output directory (default: `tests/results/intent_regression_runs`)
- `--max-cases N`: run first N cases only
- `--min-accuracy 0.80`: fail (exit code != 0) if accuracy drops below threshold
- `--print-mismatches`: print mismatches with rationale/clarifier

## Output Artifacts

Each run writes two files:
1. Case-by-case results (JSON Lines):
  - `tests/results/intent_regression_runs/intent_run_<timestamp>.jsonl`
2. Summary report:
  - `tests/results/intent_regression_runs/intent_run_<timestamp>_summary.json`

The summary includes:
- total cases
- accuracy
- clarify rate
- average confidence
- use LLM fallback rate
- confusion breakdown by expected intent

## How to Interpret Results

### Accuracy
- Target: >= **80%** exact match for stable behavior
- Some cases are intentionally ambiguous; use notes to interpret those

### Clarify Rate
- Clarifying questions should be **rare and purposeful**
- If clarify rate increases after a change, it may indicate:
  - confidence calibration too conservative
  - prompot drift
  - too many ambiguous cases

### Confusion Breakdown
If:
- `guided_study` dominiating -> prompt/heuristics are too eager
- `profession_research` overused -> signals for research are too broad
- `urgent_troubleshooting` missed -> error pattern detection needs improvement

## Updating Cases
Guidelines:
- Keep case IDs stable to track long-term regressions
- Prefer adding new cases instead of editing old ones
- If expected intent changes, document the reason in `note`

## Recommended Workflow

Recommended workflow when chaning intent logic/prompts:
1. Make code/prompt change
2. Run:
```bash
uv run python -m research_learning_agent.scripts.intent_regression --print-mismatches
```
3. Review mismatches (rationale + clarifying question)
4. Iterate until distribution and accuracy are stable

## Security / Privacy Notes
- The harness logs queries to files for local evaluation.
- Do not include secrets in canned queries.
- If run the harness on real user queries, ensure redacting sensitive content before logging.
