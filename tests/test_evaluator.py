import pytest
from core.schema import ReferenceCodeSlice, DecisionSlice
from evaluator.sandbox_runner import SandboxRunner
from evaluator.evidence_scorer import EvidenceScorer
from seeds.agent_patterns.evaluator_optimizer import SEED_EVALUATOR_OPTIMIZER

def test_sandbox_execution_success():
    sandbox = SandboxRunner()
    res = sandbox.run_code_slice_test(SEED_EVALUATOR_OPTIMIZER.reference_code)
    assert res["success"] is True
    assert res["error"] is None

def test_sandbox_execution_failure():
    sandbox = SandboxRunner()
    bad_slice = ReferenceCodeSlice(
        entry_point="bad_fn",
        language="python",
        code_content="def bad_fn(): return 10",
        test_code="def test_bad_fn(): assert bad_fn() == 99",
        dependencies=[]
    )
    res = sandbox.run_code_slice_test(bad_slice)
    assert res["success"] is False
    assert "assert 10 == 99" in str(res["error"]) or "AssertionError" in str(res["error"])

def test_evidence_scorer():
    scorer = EvidenceScorer()
    conf_success = scorer.calculate_confidence(SEED_EVALUATOR_OPTIMIZER, test_success=True)
    conf_fail = scorer.calculate_confidence(SEED_EVALUATOR_OPTIMIZER, test_success=False)
    assert conf_success > 0.8
    assert conf_fail < conf_success
