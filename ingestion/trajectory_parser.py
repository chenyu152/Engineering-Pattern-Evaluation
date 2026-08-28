import json
import logging
from typing import Dict, Any, Optional
from core.schema import (
    DecisionSlice,
    ConstraintProfile,
    TradeoffItem,
    ReferenceCodeSlice,
    EvidenceData,
    PatternCategory,
    StandardReference,
    EvidenceLevel,
    LifecycleStatus,
)

logger = logging.getLogger(__name__)

class SWETrajectoryParser:
    """
    Parses SWE-bench / SWE-agent execution trajectories into reusable bug-fixing and refactoring patterns.
    """
    def __init__(self):
        pass

    def parse_trajectory_json(self, trajectory_data: Dict[str, Any], slice_id: str) -> Optional[DecisionSlice]:
        """
        Parses a SWE-bench trajectory containing instance_id, problem_statement, patch, and test outcomes.
        """
        try:
            instance_id = trajectory_data.get("instance_id", slice_id)
            problem_statement = trajectory_data.get("problem_statement", "SWE-bench bug fixing task")
            patch = trajectory_data.get("model_patch", trajectory_data.get("patch", ""))
            test_result = trajectory_data.get("test_result", {})
            test_passed = trajectory_data.get("resolved", True)

            ref_code = ReferenceCodeSlice(
                entry_point="apply_patch",
                language="python",
                code_content=patch if patch else "# No patch provided",
                test_code=trajectory_data.get("eval_script", "def test_eval(): assert True"),
                dependencies=[]
            )

            evidence = EvidenceData(
                evidence_level=EvidenceLevel.CONTROLLED_SANDBOX if test_passed else EvidenceLevel.OBSERVED,
                source_reference=f"SWE-bench instance: {instance_id}",
                test_pass_rate=1.0 if test_passed else 0.0,
                benchmark_metrics={"resolved": test_passed}
            )

            decision = DecisionSlice(
                id=slice_id,
                pattern_name=f"Fix Pattern: {instance_id}",
                category=PatternCategory.FAULT_TOLERANCE,
                standard_reference=StandardReference.SWE_BENCH,
                problem_statement=problem_statement,
                context_constraints=ConstraintProfile(),
                considered_alternatives=[],
                chosen_solution_summary=f"Automated resolution patch for repository issue in {instance_id}",
                tradeoffs=[
                    TradeoffItem(
                        dimension="Correctness vs Regression Risk",
                        advantage="Resolves failing reproduction tests",
                        disadvantage="Local patch requires comprehensive regression checking",
                        rationale="Targeted fix minimizes side-effects"
                    )
                ],
                failure_modes=[],
                reference_code=ref_code,
                evidence=evidence,
                confidence_score=0.9 if test_passed else 0.4,
                status=LifecycleStatus.ACTIVE if test_passed else LifecycleStatus.DEPRECATED
            )
            return decision
        except Exception as e:
            logger.error(f"Failed to parse SWE trajectory: {e}")
            return None
