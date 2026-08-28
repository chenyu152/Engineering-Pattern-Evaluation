import pytest
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

def test_decision_slice_serialization():
    slice_data = DecisionSlice(
        id="test_pattern_01",
        pattern_name="Test Pattern",
        category=PatternCategory.AGENTIC_WORKFLOW,
        standard_reference=StandardReference.ANTHROPIC_AGENTIC,
        problem_statement="Test problem statement",
        context_constraints=ConstraintProfile(latency_budget_ms=100.0),
        considered_alternatives=[
            AlternativeConsidered(name="Alt A", rejected_reason="Too slow")
        ],
        chosen_solution_summary="Test solution",
        tradeoffs=[
            TradeoffItem(dimension="Cost", advantage="Cheap", disadvantage="Slow", rationale="Test")
        ],
        failure_modes=[
            FailureMode(trigger_condition="OOM", consequence="Crash", mitigation_strategy="Cap memory")
        ],
        reference_code=ReferenceCodeSlice(
            entry_point="foo",
            language="python",
            code_content="def foo(): return 1",
            test_code="def test_foo(): assert foo() == 1",
            dependencies=[]
        ),
        evidence=EvidenceData(
            evidence_level=EvidenceLevel.CONTROLLED_SANDBOX,
            source_reference="Paper XYZ",
            test_pass_rate=1.0
        ),
        confidence_score=0.95,
        status=LifecycleStatus.ACTIVE
    )

    d = slice_data.model_dump()
    assert d["id"] == "test_pattern_01"
    assert d["category"] == "Agentic_Workflow"
    assert d["standard_reference"] == "Anthropic: Building Effective Agents"

    reconstructed = DecisionSlice(**d)
    assert reconstructed.id == slice_data.id
    assert reconstructed.confidence_score == 0.95
