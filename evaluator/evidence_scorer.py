import math
from datetime import datetime, timezone
from typing import Dict, Any
from core.schema import DecisionSlice, EvidenceLevel
from config.settings import settings

class EvidenceScorer:
    """
    Computes rigorous confidence and evidence score based on:
    1. Base Evidence Level (L1 Observed=0.7, L2 Comparative=0.85, L3 Controlled_Sandbox=0.98)
    2. Sandbox test execution pass rate
    3. Time decay (Exponential decay based on last verified date)
    4. Benchmark metric completeness
    """
    def __init__(self, half_life_days: float = settings.CONFIDENCE_HALF_LIFE_DAYS):
        self.half_life_days = half_life_days

    def calculate_confidence(self, decision: DecisionSlice, test_success: bool = True) -> float:
        # Base score from Evidence Level
        base_weights = {
            EvidenceLevel.OBSERVED: 0.70,
            EvidenceLevel.COMPARATIVE: 0.85,
            EvidenceLevel.CONTROLLED_SANDBOX: 0.98,
        }
        base_score = base_weights.get(decision.evidence.evidence_level, 0.60)

        # Test execution multiplier
        test_factor = 1.0 if test_success else 0.3

        # Time decay calculation
        try:
            verified_date = datetime.strptime(decision.evidence.last_verified_at, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            delta_days = (datetime.now(timezone.utc) - verified_date).days
            # Exponential decay: 2^(-delta_days / half_life)
            decay_factor = math.pow(0.5, max(0, delta_days) / self.half_life_days)
        except Exception:
            decay_factor = 0.9

        # Benchmark completeness bonus
        benchmark_bonus = 0.05 if decision.evidence.benchmark_metrics else 0.0

        # Composite score
        confidence = (base_score * test_factor * decay_factor) + benchmark_bonus
        return max(0.0, min(1.0, round(confidence, 4)))
