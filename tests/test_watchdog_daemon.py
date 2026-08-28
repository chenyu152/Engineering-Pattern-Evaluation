import pytest
from storage.hybrid_repository import HybridRepository
from seeds.loader import seed_database
from lifecycle.dependency_checker import DependencyChecker
from lifecycle.auto_healer import AutoHealer
from lifecycle.watchdog_daemon import WatchdogDaemon
from evaluator.sandbox_runner import SandboxRunner
from evaluator.evidence_scorer import EvidenceScorer

def test_dependency_checker():
    checker = DependencyChecker()
    # Open bound >=7.0.0 should not be stale
    results = checker.check_pattern_dependencies(["pytest>=7.0.0", "redis==2.10.0"])
    assert len(results) == 2
    assert results[0]["package"] == "pytest"
    assert results[0]["is_stale"] is False
    assert results[1]["package"] == "redis"
    # redis==2.10.0 pinned to legacy v2 should be flagged stale
    assert results[1]["is_stale"] is True

def test_auto_healer_cycle():
    repo = HybridRepository()
    seed_database(repo)
    
    sandbox = SandboxRunner()
    scorer = EvidenceScorer()
    dep_checker = DependencyChecker()
    healer = AutoHealer(repo, sandbox, scorer, dep_checker)
    
    results = healer.heal_all()
    assert len(results) >= 13
    for r in results:
        assert r["test_passed"] is True
        assert r["new_status"] == "Active"

def test_watchdog_daemon_lifecycle():
    repo = HybridRepository()
    seed_database(repo)
    
    daemon = WatchdogDaemon(repository=repo, check_interval_seconds=10)
    assert daemon.is_running is False
    
    # Run one manual cycle
    results = daemon.run_cycle_now()
    assert len(results) >= 13
    assert daemon.total_runs_completed == 1
    assert daemon.last_run_time is not None
    
    # Start and stop background thread
    daemon.start()
    assert daemon.is_running is True
    daemon.stop()
    assert daemon.is_running is False
