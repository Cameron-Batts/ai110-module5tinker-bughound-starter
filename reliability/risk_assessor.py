"""Conservative static checks; scores are heuristics, never correctness probabilities."""

import ast
from difflib import SequenceMatcher
from typing import Dict, List

MAX_CHANGE_RATIO = 0.5


def assess_risk(original_code: str, fixed_code: str, issues: List[Dict[str, str]]) -> Dict[str, object]:
    def blocked(reason):
        return {"score": 0, "level": "high", "reasons": [reason], "should_autofix": False}

    if not isinstance(original_code, str) or not isinstance(fixed_code, str):
        return blocked("Original and proposed code must be strings. Human review required.")
    if not fixed_code.strip():
        return blocked("No fix was produced.")
    if not isinstance(issues, list) or any(
        not isinstance(issue, dict)
        or any(not isinstance(issue.get(field), str) or not issue[field].strip()
               for field in ("type", "severity", "msg"))
        or issue["severity"].strip().lower() not in {"low", "medium", "high"}
        for issue in issues
    ):
        return blocked("Invalid issue records. Human review required.")
    try:
        fixed_tree = ast.parse(fixed_code)
    except (SyntaxError, ValueError):
        return blocked("Proposed fix has invalid Python syntax. Human review required.")
    try:
        original_tree = ast.parse(original_code)
    except (SyntaxError, ValueError):
        return blocked("Original code cannot be parsed for comparison. Human review required.")

    score, reasons = 100, []
    for issue in issues:
        severity = issue["severity"].strip().lower()
        score -= {"high": 40, "medium": 20, "low": 5}[severity]
        reasons.append(f"{severity.title()} severity issue detected.")
    original_lines = original_code.strip().splitlines()
    fixed_lines = fixed_code.strip().splitlines()
    if len(fixed_lines) < len(original_lines) * 0.5:
        score -= 20
        reasons.append("Fixed code is much shorter than original.")
    original_returns = sum(isinstance(node, ast.Return) for node in ast.walk(original_tree))
    fixed_returns = sum(isinstance(node, ast.Return) for node in ast.walk(fixed_tree))
    if fixed_returns < original_returns:
        score -= 30
        reasons.append("Return statements may have been removed.")
    original_bare = sum(isinstance(n, ast.ExceptHandler) and n.type is None for n in ast.walk(original_tree))
    fixed_bare = sum(isinstance(n, ast.ExceptHandler) and n.type is None for n in ast.walk(fixed_tree))
    if fixed_bare < original_bare:
        score -= 5
        reasons.append("Bare except was modified, verify correctness.")

    ratio = 1 - SequenceMatcher(None, original_lines, fixed_lines, autojunk=False).ratio()
    ast_changed = ast.dump(original_tree, include_attributes=False) != ast.dump(fixed_tree, include_attributes=False)
    if ratio > MAX_CHANGE_RATIO:
        reasons.append("Large rewrite exceeds the 50% line-change threshold. Human review required.")
    if ast_changed:
        reasons.append("Executable structure changed; behavioral correctness needs human review.")
    score = max(0, min(100, score))
    level = "low" if score >= 75 else "medium" if score >= 40 else "high"
    eligible = level == "low" and score >= 85 and ratio <= MAX_CHANGE_RATIO and not ast_changed
    if level == "low" and score < 85:
        reasons.append("Auto-fix requires a score of at least 85.")
    if not reasons:
        reasons.append("No static policy issue detected; this is not a runtime correctness guarantee.")
    return {"score": score, "level": level, "reasons": reasons,
            "change_ratio": ratio, "executable_structure_changed": ast_changed,
            "should_autofix": eligible}
