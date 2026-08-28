import logging
from typing import List, Dict, Any
from core.schema import DecisionSlice, LifecycleStatus
from storage.hybrid_repository import HybridRepository
from .evidence_scorer import EvidenceScorer
from .sandbox_runner import SandboxRunner

logger = logging.getLogger(__name__)

class StaleDetector:
    """
    Monitors decision slices for dependency deprecations, aging decay,
    and triggers sandbox re-verification.
    """
    def __init__(self, repository: HybridRepository, sandbox: SandboxRunner, scorer: EvidenceScorer):
        self.repository = repository
        self.sandbox = sandbox
        self.scorer = scorer

    def audit_all_patterns(self) -> List[Dict[str, Any]]:
        """Audits all patterns in the repository, re-tests runnable code slices, and updates confidence."""
        audit_results = []
        patterns = self.repository.list_all()

        for pattern in patterns:
            logger.info(f"Auditing pattern: {pattern.id} ({pattern.pattern_name})")
            
            # Execute sandbox test
            test_res = self.sandbox.run_code_slice_test(pattern.reference_code)
            is_valid = test_res.get("success", False)

            # Re-score confidence
            new_confidence = self.scorer.calculate_confidence(pattern, test_success=is_valid)
            pattern.confidence_score = new_confidence

            # Update lifecycle status
            if new_confidence < 0.4 or not is_valid:
                pattern.status = LifecycleStatus.STALE
            elif new_confidence < 0.2:
                pattern.status = LifecycleStatus.DEPRECATED
            else:
                pattern.status = LifecycleStatus.ACTIVE

            # Persist updated pattern
            self.repository.save_decision_slice(pattern)

            audit_results.append({
                "id": pattern.id,
                "pattern_name": pattern.pattern_name,
                "test_passed": is_valid,
                "new_confidence": new_confidence,
                "status": pattern.status.value,
                "error": test_res.get("error")
            })

        return audit_results
