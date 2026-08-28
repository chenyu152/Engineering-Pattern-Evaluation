import pytest
from evaluator.sandbox_runner import SandboxRunner
from seeds.loader import GOLDEN_SEEDS

@pytest.mark.parametrize("seed", GOLDEN_SEEDS, ids=[s.id for s in GOLDEN_SEEDS])
def test_golden_seed_sandbox_execution(seed):
    """Verifies that all 13 golden seeds execute cleanly and pass their unit tests in sandbox."""
    sandbox = SandboxRunner()
    res = sandbox.run_code_slice_test(seed.reference_code)
    assert res["success"] is True, f"Failed sandbox test for {seed.id}: {res.get('error')}"
    assert res["returncode"] == 0
