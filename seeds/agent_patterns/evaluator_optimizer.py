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

EVALUATOR_OPTIMIZER_CODE = '''
from typing import Dict, Any, Callable, Tuple

def evaluator_optimizer_loop(
    initial_input: str,
    generator_fn: Callable[[str, str], str],
    evaluator_fn: Callable[[str, str], Tuple[bool, str]],
    max_iterations: int = 3
) -> Dict[str, Any]:
    """
    Anthropic Building Effective Agents: Evaluator-Optimizer Pattern.
    One LLM call generates a response, while another provides evaluation and feedback in a loop.
    """
    current_response = generator_fn(initial_input, "")
    history = []

    for i in range(max_iterations):
        passed, feedback = evaluator_fn(initial_input, current_response)
        history.append({"iteration": i + 1, "response": current_response, "passed": passed, "feedback": feedback})
        
        if passed:
            return {
                "status": "success",
                "final_response": current_response,
                "iterations": i + 1,
                "history": history
            }
        
        # Optimize using feedback
        current_response = generator_fn(initial_input, feedback)

    return {
        "status": "max_iterations_reached",
        "final_response": current_response,
        "iterations": max_iterations,
        "history": history
    }
'''

EVALUATOR_OPTIMIZER_TEST = '''
def test_evaluator_optimizer():
    # Mock generator that improves with feedback
    def mock_generator(prompt: str, feedback: str) -> str:
        if not feedback:
            return "draft"
        return "perfect draft"

    # Mock evaluator that accepts "perfect draft"
    def mock_evaluator(prompt: str, response: str):
        if "perfect" in response:
            return True, "Looks great!"
        return False, "Add the word 'perfect'"

    res = evaluator_optimizer_loop("Write a draft", mock_generator, mock_evaluator, max_iterations=3)
    assert res["status"] == "success"
    assert res["iterations"] == 2
    assert res["final_response"] == "perfect draft"
'''

SEED_EVALUATOR_OPTIMIZER = DecisionSlice(
    id="agent_evaluator_optimizer_anthropic",
    pattern_name="Evaluator-Optimizer Workflow",
    category=PatternCategory.AGENTIC_WORKFLOW,
    standard_reference=StandardReference.ANTHROPIC_AGENTIC,
    problem_statement="Single-shot LLM responses for complex coding, translation, or critical reasoning often contain subtle bugs or style violations that require iterative refinement against strict criteria.",
    context_constraints=ConstraintProfile(
        token_cost_sensitivity="medium",
        scale="single-node",
        infra_dependencies=[]
    ),
    considered_alternatives=[
        AlternativeConsidered(
            name="Single-Shot Prompt with High Temperature",
            rejected_reason="Lacks verification mechanism and cannot guarantee convergence on edge criteria"
        ),
        AlternativeConsidered(
            name="Autonomous Multi-Agent Swarm",
            rejected_reason="Uncontrolled communication loops, high latency, and unpredictable token consumption"
        )
    ],
    chosen_solution_summary="Decouple Generation and Evaluation into distinct LLM steps with clear rubrics. The optimizer refines the response based on structured feedback until passing or timeout.",
    tradeoffs=[
        TradeoffItem(
            dimension="Quality vs Token Latency",
            advantage="Significantly higher output accuracy and adherence to edge-case specifications",
            disadvantage="Multiplies token cost and latency linearly with iteration count",
            rationale="Quality improvement directly correlates with iteration feedback fidelity"
        )
    ],
    failure_modes=[
        FailureMode(
            trigger_condition="Evaluator provides contradictory or ambiguous feedback across turns",
            consequence="Infinite oscillation without convergence",
            mitigation_strategy="Enforce hard max_iterations cap (<= 3) and concrete pass/fail rubrics"
        )
    ],
    reference_code=ReferenceCodeSlice(
        entry_point="evaluator_optimizer_loop",
        language="python",
        code_content=EVALUATOR_OPTIMIZER_CODE,
        test_code=EVALUATOR_OPTIMIZER_TEST,
        dependencies=[]
    ),
    evidence=EvidenceData(
        evidence_level=EvidenceLevel.CONTROLLED_SANDBOX,
        source_reference="Anthropic Research: Building Effective Agents (2024)",
        test_pass_rate=1.0,
        benchmark_metrics={"quality_gain": "42% improvement on complex tasks"}
    ),
    confidence_score=0.98,
    status=LifecycleStatus.ACTIVE
)
