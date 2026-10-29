# BugHound Model Card

Cameron Batts

## Purpose and workflow

BugHound is an experimental agent-style assistant that proposes Python edits and explains a static review decision. Its PLAN, ANALYZE, ACT, TEST and REFLECT steps are orchestration labels; the TEST step parses and scores a proposal rather than executing its behavior. The app displays proposed code and an eligibility flag; it does not automatically write source files.

## Current review policy

Issue records must contain nonempty type, severity and msg strings with a recognized severity. Invalid records trigger fallback at the agent boundary and fail closed when sent directly to the risk assessor.

Both original and proposed snippets must parse. High, Medium and Low issue severities deduct 40, 20 and 5 points. Return removal, severe shortening and changed bare handlers have additional deductions. Scores are heuristic diagnostics, not calibrated correctness probabilities.

Eligibility requires low risk, score at least 85, line-change ratio at most 0.5, and an unchanged executable AST. Changed return values and other executable edits require human review even with score 100. This is deliberately conservative: most useful code repairs will be review-only proposals. AST equality does not prove a program is correct or free from context-dependent effects.

## Heuristics and source preservation

Actual print calls and bare handlers are found with AST inspection. TODO checks inspect comments. Print-like text inside comments and strings is no longer treated as a call.

Source-span edits preserve comments, quoted text and UTF-8 positions. Added logging imports follow a module docstring and future imports. Only simple one-argument print calls are proposed for logging conversion; more complicated print behavior remains for review. Proposed changes are never executed by these static checks.

## Verified reliability evidence

The original 11 offline tests continue to pass. Twelve additional cases check large rewrites, changed return values, formatting-only eligibility, comment/string false positives, malformed issues, invalid originals, UTF-8 positions, future imports and exception-handler indentation. All 23 tests passed.

No live Gemini calls were made during this verification. Mock clients exercise schema failure and fallback. Passing tests establishes the covered behaviors, not arbitrary fix correctness.

## Historical model observations

The earlier model card recorded Gemini proposing input validation that changed exception behavior, and converting diagnostic printing while retaining greeting output. These are historical observations from the previous policy, not fresh results. A proposal previously shown as auto-fix eligible may now require review because executable structure changed.

## Limitations and misuse

The heuristic detector is intentionally narrow. A function named print may shadow the builtin. Logging conversion can change output semantics, and narrowing a bare handler changes which exceptions are caught. A model may omit a serious issue; a heuristic score cannot compensate for that. Large diff and AST checks do not prove safety. Standalone parsing may reject valid context-dependent fragments.

Keep human review for executable changes, inspect proposed diffs, and run appropriate project tests in a controlled environment before using a proposal. Avoid sharing secrets or private code with an external model without appropriate authorization.
