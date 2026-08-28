import pytest
from storage.hybrid_repository import HybridRepository
from ingestion.github_live_miner import GitHubLiveMiner

def test_github_live_miner_extract_pr():
    repo = HybridRepository()
    miner = GitHubLiveMiner(repository=repo)

    mock_pr = {
        "number": 1042,
        "title": "Refactor distributed cache aside to prevent stampede",
        "body": "## Problem\nHeavy concurrent reads on user cache caused stampede.\n## Solution\nIntroduced single-flight mutex lock.",
        "html_url": "https://github.com/example/repo/pull/1042",
        "state": "closed",
        "merged_at": "2026-05-01T12:00:00Z"
    }

    decision = miner.extract_decision_from_pr(mock_pr, "example/repo")
    assert decision is not None
    assert decision.id == "github_example_repo_pr_1042"
    assert "single-flight mutex lock" in decision.problem_statement or "stampede" in decision.problem_statement
    assert decision.category.value == "Data_Persistence"
