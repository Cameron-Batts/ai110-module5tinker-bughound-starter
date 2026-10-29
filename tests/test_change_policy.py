"""Conservative eligibility and syntax-aware proposal regressions."""

import ast
from bughound_agent import BugHoundAgent
from reliability.risk_assessor import assess_risk


def test_changed_return_value_requires_review():
    risk = assess_risk("def f():\n    return 1\n", "def f():\n    return 999\n", [])
    assert risk["score"] == 100
    assert not risk["should_autofix"]
    assert risk["executable_structure_changed"]


def test_large_valid_rewrite_requires_review():
    risk = assess_risk("x = 1\ny = 2\n", "a = 3\nb = 4\nc = 5\n", [])
    assert not risk["should_autofix"]
    assert risk["change_ratio"] > .5
    assert any("rewrite" in reason.lower() for reason in risk["reasons"])


def test_small_formatting_change_can_be_eligible():
    original = "x = 1\ny = 2\nz = x + y\n"
    fixed = "x = 1\ny = 2\nz = x+y\n"
    risk = assess_risk(original, fixed, [])
    assert risk["should_autofix"]
    assert not risk["executable_structure_changed"]


def test_comment_print_is_not_an_issue_or_a_rewrite():
    code = "# print('not executable')\nx = 1\n"
    result = BugHoundAgent().run(code)
    assert result["issues"] == []
    assert result["fixed_code"] == code


def test_string_print_is_not_an_issue_or_a_rewrite():
    code = 'message = "print(hello) TODO"\n'
    result = BugHoundAgent().run(code)
    assert result["issues"] == []
    assert result["fixed_code"] == code


def test_real_print_proposal_preserves_quoted_and_comment_text():
    code = 'message = "print(keep)"\n# print(keep)\nprint("hello")\n'
    result = BugHoundAgent().run(code)
    assert 'message = "print(keep)"' in result["fixed_code"]
    assert '# print(keep)' in result["fixed_code"]
    assert 'logging.info("hello")' in result["fixed_code"]
    assert not result["risk"]["should_autofix"]


def test_unicode_before_print_has_correct_source_offsets():
    code = 'message = "hi 😊"; print("hello")\n'
    fixed = BugHoundAgent().run(code)["fixed_code"]
    assert 'message = "hi 😊"; logging.info("hello")' in fixed
    ast.parse(fixed)


def test_import_insertion_preserves_future_import_rules():
    code = '"""Module docs."""\nfrom __future__ import annotations\nprint("hello")\n'
    fixed = BugHoundAgent().run(code)["fixed_code"]
    ast.parse(fixed)
    assert fixed.index('from __future__') < fixed.index('import logging')


def test_invalid_issue_records_fail_closed():
    risk = assess_risk("x=1\n", "x=1\n", [{"severity": "banana"}])
    assert not risk["should_autofix"]
    assert risk["level"] == "high"


def test_invalid_original_needs_review():
    risk = assess_risk("if broken", "x = 1\n", [])
    assert not risk["should_autofix"]


def test_bare_except_proposal_keeps_original_indentation():
    code = 'def f():\n    try:\n        return 1\n    except:\n        return 0\n'
    result = BugHoundAgent().run(code)
    ast.parse(result["fixed_code"])
    assert '    except Exception as e:\n        return 0' in result["fixed_code"]
    assert not result["risk"]["should_autofix"]


def test_todo_in_comment_is_detected():
    result = BugHoundAgent().run("# TODO: finish this\nx = 1\n")
    assert any(issue["type"] == "Maintainability" for issue in result["issues"])
