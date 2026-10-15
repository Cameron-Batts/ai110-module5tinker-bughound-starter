from bughound_agent import BugHoundAgent
from reliability.risk_assessor import assess_risk


class InvalidIssueClient:
    def complete(self, system_prompt, user_prompt):
        return '[{"severity": "banana"}]'


def test_invalid_issue_schema_falls_back_to_heuristics():
    agent = BugHoundAgent(client=InvalidIssueClient())
    issues = agent.analyze("print('hello')\n")

    assert any(issue["type"] == "Code Quality" for issue in issues)
    assert any(
        "Falling back to heuristics" in entry["message"]
        for entry in agent.logs
    )


def test_score_of_80_requires_human_review():
    result = assess_risk(
        original_code="value = 1\n",
        fixed_code="value = 2\n",
        issues=[
            {
                "type": "Maintainability",
                "severity": "Medium",
                "msg": "A behavior change needs review.",
            }
        ],
    )

    assert result["score"] == 80
    assert result["should_autofix"] is False


def test_invalid_python_is_high_risk_and_blocks_autofix():
    result = assess_risk(
        original_code="print('hello')\n",
        fixed_code="if True print('hello')\n",
        issues=[
            {
                "type": "Code Quality",
                "severity": "Low",
                "msg": "Use logging.",
            }
        ],
    )

    assert result["should_autofix"] is False
    assert result["level"] == "high"
    assert any("syntax" in reason.lower() for reason in result["reasons"])
