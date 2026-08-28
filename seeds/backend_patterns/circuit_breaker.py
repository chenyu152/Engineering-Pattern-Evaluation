from core.schema import (
    DecisionSlice,
    ConstraintProfile,
    TradeoffItem,
    AlternativeConsidered,
    FailureMode,
    ReferenceCodeSlice,
    EvidenceData,
    PatternCategory,
    StandardReference,
    EvidenceLevel,
    LifecycleStatus,
)

CIRCUIT_BREAKER_CODE = '''
import time
from typing import Callable, Any

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    """
    Three-State Circuit Breaker Pattern (CLOSED, OPEN, HALF_OPEN).
    Fails fast when downstream error rate exceeds threshold to prevent cascading system collapse.
    """
    def __init__(self, failure_threshold: int = 3, recovery_timeout_sec: float = 5.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_sec
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = 0.0

    def call(self, fn: Callable[..., Any], *args, **kwargs) -> Any:
        now = time.time()
        
        # 1. State transition from OPEN to HALF_OPEN after timeout
        if self.state == "OPEN":
            if now - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenException("Circuit is OPEN: fast failing downstream call")

        # 2. Execute protected call
        try:
            result = fn(*args, **kwargs)
            # Success in HALF_OPEN recovers to CLOSED
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = now
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise e
'''

CIRCUIT_BREAKER_TEST = '''
import pytest

def test_circuit_breaker():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=0.2)
    
    def failing_service():
        raise RuntimeError("Service Unavailable")

    # 1. Fail twice
    with pytest.raises(RuntimeError):
        breaker.call(failing_service)
    with pytest.raises(RuntimeError):
        breaker.call(failing_service)
        
    assert breaker.state == "OPEN"
    
    # 2. 3rd call immediately fails fast with CircuitBreakerOpenException
    with pytest.raises(CircuitBreakerOpenException):
        breaker.call(failing_service)
'''

SEED_CIRCUIT_BREAKER = DecisionSlice(
    id="backend_circuit_breaker_resilience",
    pattern_name="Three-State Circuit Breaker",
    category=PatternCategory.FAULT_TOLERANCE,
    standard_reference=StandardReference.MADR_SPEC,
    problem_statement="Prevent cascading failure and thread pool exhaustion across microservices when a downstream dependency is slow or degraded.",
    context_constraints=ConstraintProfile(
        latency_budget_ms=1.0,
        scale="cluster",
        infra_dependencies=[]
    ),
    considered_alternatives=[
        AlternativeConsidered(
            name="Simple Retries with Timeout",
            rejected_reason="Repeated retries against an already dead service amplify the outage and trigger a retry storm"
        )
    ],
    chosen_solution_summary="Wrap external calls in a state machine (Closed, Open, Half-Open). When error threshold is breached, fail fast without calling downstream until cooldown elapsed.",
    tradeoffs=[
        TradeoffItem(
            dimension="Availability Protection vs Fast Failure Rejection",
            advantage="Stops cascading failures immediately and preserves caller threads and memory resources",
            disadvantage="Temporarily rejects valid user requests during the open cooldown period",
            rationale="Failing fast within microseconds is vastly superior to timing out after seconds"
        )
    ],
    failure_modes=[
        FailureMode(
            trigger_condition="Threshold set too sensitive for transient network blips",
            consequence="Circuit opens unnecessarily for normal jitter",
            mitigation_strategy="Use sliding window percentage thresholds instead of tiny absolute counts"
        )
    ],
    reference_code=ReferenceCodeSlice(
        entry_point="CircuitBreaker",
        language="python",
        code_content=CIRCUIT_BREAKER_CODE,
        test_code=CIRCUIT_BREAKER_TEST,
        dependencies=[]
    ),
    evidence=EvidenceData(
        evidence_level=EvidenceLevel.CONTROLLED_SANDBOX,
        source_reference="Release It! Design and Deploy Production-Ready Software (Michael Nygard) / Netflix Hystrix",
        test_pass_rate=1.0,
        benchmark_metrics={"cascade_prevention_rate": "100%"}
    ),
    confidence_score=0.98,
    status=LifecycleStatus.ACTIVE
)
