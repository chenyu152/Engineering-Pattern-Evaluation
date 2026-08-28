from typing import List, Dict, Any
from core.schema import (
    TaskAnalysisResult,
    DecisionSlice,
    TradeoffComparison,
)

class TradeoffAdvisor:
    """
    Analyzes candidate DecisionSlices against user constraints and outputs
    a structured Trade-off Matrix with positive/negative implications and failure boundaries.
    """
    def __init__(self):
        pass

    def evaluate_candidates(
        self,
        task_analysis: TaskAnalysisResult,
        candidate_matches: List[Dict[str, Any]]
    ) -> List[TradeoffComparison]:
        comparisons = []
        for i, match in enumerate(candidate_matches):
            slice_obj: DecisionSlice = match["slice"]
            composite_score: float = match["composite_score"]

            pros = [f"{t.dimension}: {t.advantage}" for t in slice_obj.tradeoffs]
            cons = [f"{t.dimension}: {t.disadvantage}" for t in slice_obj.tradeoffs]
            failure_risks = [f"{f.trigger_condition} -> {f.consequence}" for f in slice_obj.failure_modes]

            # Determine recommendation verdict
            if i == 0 and composite_score >= 0.65:
                verdict = "STRONGLY_RECOMMENDED"
            elif composite_score >= 0.45:
                verdict = "VIABLE_ALTERNATIVE"
            else:
                verdict = "NOT_RECOMMENDED"

            comparisons.append(TradeoffComparison(
                candidate_id=slice_obj.id,
                pattern_name=slice_obj.pattern_name,
                suitability_score=round(composite_score, 3),
                pros=pros or [slice_obj.chosen_solution_summary],
                cons=cons or ["Operational maintenance required"],
                critical_failure_risks=failure_risks or ["Improper configuration under edge load"],
                recommendation_verdict=verdict
            ))
        return comparisons
