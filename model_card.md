# BugHound Mini Model Card

## 1) System overview

BugHound is an experimental debugging assistant for students learning agentic workflows. It analyzes Python snippets, proposes changes, and recommends whether a proposed fix needs human review. The app displays proposed code; its auto-fix flag is a recommendation, not evidence that a file was changed.

## 2) Workflow

- PLAN: Log the planned scan and fix workflow.
- ANALYZE: Use heuristic rules offline or ask Gemini for structured issue records.
- ACT: Propose a heuristic or Gemini-generated fix.
- TEST: Check proposed Python syntax and apply risk-scoring rules.
- REFLECT: Recommend auto-fix only when the risk is low and the score is at least 85.

The heuristic analyzer searches for print calls, bare exception handlers, and TODO text. Gemini uses prompt templates to analyze code and propose fixes. Invalid JSON, invalid issue records, or unavailable model output trigger heuristic fallback.

These reliability checks do not execute the proposed code or prove that its behavior is correct.

## 3) Inputs and outputs

I tested short functions, a try/except function, a mostly clean function, and comments-only input.

| Input and mode | Observed result |
| --- | --- |
| cleanish.py, heuristic | No issues; unchanged code; score 100; low risk; auto-fix YES, with nothing to apply. |
| mixed_issues.py, heuristic, terminal file | Print, bare except, and TODO detected; score 30; high risk; auto-fix NO. |
| Comments-only input, heuristic | Print text inside a comment triggered a false positive; unnecessary logging import and comment rewrite; score 75; auto-fix NO. |
| mixed_issues.py, Gemini, app sample | Three issues detected; TODO and print rated Low, bare except rated High; score 45; medium risk; auto-fix NO. |
| print_spam.py, Gemini, terminal file | One Low issue; diagnostic print replaced with logging; greeting prints preserved; score 95; low risk; auto-fix YES. |

The app embeds sample snippets that differ slightly from files in sample_code, so cross-mode comparisons are qualitative rather than controlled measurements.

## 4) Reliability rules and design decisions

### Strict analysis validation

Previously, a JSON record containing only an invalid severity was accepted with default fields. Now every issue must have nonempty string fields for type, severity, and msg. Severity must be Low, Medium, or High, ignoring case. A malformed record rejects the response and triggers heuristic fallback. A valid empty array remains acceptable.

### Severity deductions

High, Medium, and Low issues deduct 40, 20, and 5 points respectively. This encourages review when serious issues are present.

False positive: a correctly repaired serious issue can still cause rejection because the score uses original issue severity.
False negative: a model can omit or underrate an issue, leaving an unsafe fix with a high score.

### Return-removal check

If the original contains "return" and the proposal does not, 30 points are deducted.

False positive: the word can occur only in a comment or string.
False negative: one return can remain while another is removed, or a return value can change without triggering the rule.

### Syntax guardrail

The risk assessor parses proposed code using ast.parse without executing it. Invalid syntax produces high risk, score 0, and no auto-fix.

False positive: a valid fragment requiring surrounding context may be rejected as a standalone snippet.
False negative: syntactically valid code can still raise runtime errors or change behavior.

### Stricter auto-fix policy

The previous policy allowed any low-risk score, starting at 75. Auto-fix now requires at least 85. A controlled test with score 80 changed from YES to NO while retaining the same score and low-risk label. The label and permission threshold serve different purposes.

## 5) Observed failure modes

1. The heuristic analyzer treated print text inside a comment as an actual call. Its fixer added logging and edited the comment unnecessarily.
2. Before the syntax guardrail, a controlled test showed that invalid Python could be approved for auto-fix. The new guardrail rejects it.
3. Gemini added validate_input to the mixed-issues function and called it before the try block. Invalid inputs now raise TypeError instead of returning 0 as the original broad handler did. This changes behavior and requires review.
4. The app originally connected its heuristic option to MockClient. This produced simulated LLM traces and a placeholder fix. I changed that option to client=None so it uses the actual heuristic analyzer and fixer.

## 6) Heuristic versus Gemini

Heuristics consistently detected the three text patterns in the mixed-issues sample. They rated TODO as Medium, while Gemini rated it Low in the observed run. Both modes required human review.

For print_spam.py, the heuristic fixer would replace every print call. Gemini instead changed the diagnostic print and retained the user-facing greetings. However, it also added logging.basicConfig at module scope. The score of 95 did not reflect the possible effect on application-wide logging.

Gemini's mixed-issues fix added input validation and narrowed the exception handler to ZeroDivisionError. Those changes require understanding intended behavior. MockClient results were simulated and are not counted as real Gemini evidence.

## 7) Human-in-the-loop decision

Invalid Python must never be approved for auto-fix. This guardrail is implemented in reliability/risk_assessor.py.

Trigger: the proposed code fails Python parsing.
Decision: high risk, score 0, no auto-fix.
Message: "Proposed fix has invalid Python syntax. Human review required."

A syntactically valid change to exception handling or validation can also require human review. The mixed-issues Gemini proposal is an example: its new TypeError behavior may be intentional, but the agent cannot decide that from syntax alone.

## 8) Tests and future improvement

Before implementation, the three new regression tests failed and the eight existing tests passed. After implementation, all 11 tests passed.

The new tests protect invalid-issue fallback, human review at score 80, and rejection of invalid Python syntax.

A next improvement is to inspect print calls using Python's AST rather than substring matching. A measurable acceptance criterion is that comments or strings containing "print(" cause no print-call issue and no rewrite, while an actual print call remains detectable.
