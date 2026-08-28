import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from core.schema import DecisionSlice, LifecycleStatus
from storage.hybrid_repository import HybridRepository
from evaluator.sandbox_runner import SandboxRunner
from evaluator.evidence_scorer import EvidenceScorer
from .dependency_checker import DependencyChecker

logger = logging.getLogger(__name__)

class AutoHealer:
    """
    Automated Lifecycle State Machine & Health Self-Healing Engine:
    - Runs periodic Sandbox Re-benchmarks.
    - Evaluates Dependency freshness.
    - Transitions states: Active <-> Stale -> Deprecated.
    - Logs diagnostic snapshots for self-healing.
    """
    def __init__(
        self,
        repository: HybridRepository,
        sandbox: SandboxRunner,
        scorer: EvidenceScorer,
        dep_checker: DependencyChecker
    ):
        self.repository = repository
        self.sandbox = sandbox
        self.scorer = scorer
        self.dep_checker = dep_checker
        self.healing_logs: List[Dict[str, Any]] = []

    def inspect_and_heal_pattern(self, pattern: DecisionSlice) -> Dict[str, Any]:
        """Runs healthcheck on a single pattern and auto-heals its confidence score & state."""
        # 1. Run sandbox test
        test_res = self.sandbox.run_code_slice_test(pattern.reference_code)
        test_passed = test_res.get("success", False)

        # 2. Check dependencies
        dep_res = self.dep_checker.check_pattern_dependencies(pattern.reference_code.dependencies)
        has_major_dep_upgrade = any(d["is_stale"] for d in dep_res)

        # 3. Recalculate confidence
        old_confidence = pattern.confidence_score
        old_status = pattern.status
        new_confidence = self.scorer.calculate_confidence(pattern, test_success=test_passed)

        if has_major_dep_upgrade:
            new_confidence = max(0.2, new_confidence - 0.15)

        pattern.confidence_score = new_confidence

        # 4. State Machine Transition
        if not test_passed:
            pattern.status = LifecycleStatus.STALE
            action_taken = "DEMOTED_TO_STALE_TEST_FAILURE"
        elif has_major_dep_upgrade:
            pattern.status = LifecycleStatus.STALE
            action_taken = "DEMOTED_TO_STALE_MAJOR_DEP_UPGRADE"
        elif new_confidence < 0.3:
            pattern.status = LifecycleStatus.DEPRECATED
            action_taken = "DEMOTED_TO_DEPRECATED_LOW_CONFIDENCE"
        else:
            pattern.status = LifecycleStatus.ACTIVE
            action_taken = "RESTORED_ACTIVE" if old_status != LifecycleStatus.ACTIVE else "MAINTAINED_ACTIVE"

        pattern.evidence.last_verified_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Save to repository
        self.repository.save_decision_slice(pattern)

        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pattern_id": pattern.id,
            "pattern_name": pattern.pattern_name,
            "old_status": old_status.value,
            "new_status": pattern.status.value,
            "old_confidence": old_confidence,
            "new_confidence": new_confidence,
            "test_passed": test_passed,
            "action_taken": action_taken,
            "dependencies_checked": dep_res,
            "error_detail": test_res.get("error")
        }
        self.healing_logs.append(audit_entry)
        return audit_entry

    def heal_all(self) -> List[Dict[str, Any]]:
        """Scans all patterns in repository and applies self-healing lifecycle logic."""
        all_patterns = self.repository.list_all()
        results = []
        for p in all_patterns:
            res = self.inspect_and_heal_pattern(p)
            results.append(res)
        return results
