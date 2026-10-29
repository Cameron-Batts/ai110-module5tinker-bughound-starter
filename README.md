# BugHound

Cameron Batts

An experimental Python debugging assistant that analyzes a snippet, proposes a change and applies a conservative static-review policy. It provides an offline heuristic mode and optional Gemini proposals.

## Review policy

A score is a heuristic, not a probability that a fix is correct. A proposal is eligible only when all of these checks pass:

- Both snippets parse as standalone Python.
- Issue records have the expected nonempty fields and recognized severities.
- The heuristic score is at least 85 and the risk label is low.
- The line-change ratio is at most 50%.
- The original and proposed ASTs have identical executable structure.

Executable changes require human review even when their score is 100. This intentionally routes logging replacements, modified return values and changed exception handling for review. Formatting/comment-only changes can be eligible if the other conditions hold. The eligibility flag does not write files, and AST equivalence is not a general runtime correctness proof.

## Heuristics

The analyzer identifies actual print calls and bare exception handlers through Python's AST. TODO checks inspect comments. Strings and comments containing print-like text no longer trigger print-call changes.

The proposal editor changes source spans rather than replacing every print-like substring. It preserves quoted/comment text, UTF-8 offsets and future-import placement. More complex print signatures remain for manual attention. Proposed snippets are parsed rather than executed by these checks.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run bughound_app.py
```

Choose Heuristic only for the offline workflow. Gemini mode requires a locally configured API key. Provider charges may apply when generation is requested.

## Verified tests

```bash
python3 -m pytest -q
```

```text
23 passed
```

Tests cover the existing workflow, invalid model-response fallback, invalid Python, score thresholds, changed return values, large rewrites, comment/string false positives, UTF-8 source edits and future imports. Model clients in these tests are offline/mocked; live Gemini generation was not rerun.

## Examples

- A comment containing print-like text: no print issue or logging rewrite.
- A real one-argument print call: a logging proposal is shown, with human review required.
- A valid function changing return 1 to return 999: score can remain 100, but automatic eligibility is false.
- An invalid proposed snippet: high risk, score 0, automatic eligibility false.

The model card distinguishes historical generation observations from the current static-policy checks. The original starter's provenance remains visible through this repository's GitHub fork lineage.
