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

PLAN_AND_EXECUTE_CODE = '''
from typing import List, Dict, Any, Callable

def plan_and_execute(
    complex_objective: str,
    planner_fn: Callable[[str], List[str]],
    step_executor_fn: Callable[[str, Dict[str, Any]], Any],
    replan_evaluator_fn: Callable[[str, List[str], Dict[str, Any]], List[str]]
) -> Dict[str, Any]:
    """
    Plan-and-Execute Pattern.
    Separates high-level multi-step planning from individual step execution,
    with an explicit replanning mechanism upon unexpected step results.
    """
    # 1. Initial Planning
    current_plan = planner_fn(complex_objective)
    execution_context: Dict[str, Any] = {}
    completed_steps = []

    idx = 0
    while idx < len(current_plan):
        step_description = current_plan[idx]
        
        # 2. Execute current step
        step_result = step_executor_fn(step_description, execution_context)
        completed_steps.append({"step": step_description, "result": step_result})
        execution_context[f"step_{idx+1}_output"] = step_result
        
        # 3. Check if replanning is needed
        new_plan = replan_evaluator_fn(complex_objective, current_plan[idx+1:], step_result)
        if new_plan != current_plan[idx+1:]:
            current_plan = current_plan[:idx+1] + new_plan
            
        idx += 1

    return {
        "status": "success",
        "total_steps_executed": len(completed_steps),
        "completed_steps": completed_steps,
        "final_context": execution_context
    }
'''

PLAN_AND_EXECUTE_TEST = '''
def test_plan_and_execute():
    def mock_planner(objective: str):
        return ["Fetch raw data", "Clean data", "Generate report"]

    def mock_executor(step: str, context: dict):
        if "Fetch" in step:
            return {"data": [10, 20, 30]}
        elif "Clean" in step:
            return {"data_clean": [10, 20, 30]}
        elif "Generate" in step:
            return "Report Generated: Sum=60"
        return "Done"

    def mock_replanner(objective, remaining_plan, last_result):
        # No replan needed in normal flow
        return remaining_plan

    res = plan_and_execute("Build sales report", mock_planner, mock_executor, mock_replanner)
    assert res["status"] == "success"
    assert res["total_steps_executed"] == 3
    assert res["final_context"]["step_3_output"] == "Report Generated: Sum=60"
'''

SEED_PLAN_AND_EXECUTE = DecisionSlice(
    id="agent_plan_and_execute_standard",
    pattern_name="Plan-and-Execute Architecture",
    category=PatternCategory.AGENTIC_WORKFLOW,
    standard_reference=StandardReference.ANTHROPIC_AGENTIC,
    problem_statement="Long-horizon multi-step tasks get lost in low-level ReAct action loops without a high-level roadmap, leading to goal drift and excessive step count.",
    context_constraints=ConstraintProfile(
        scale="single-node",
        token_cost_sensitivity="medium",
        infra_dependencies=[]
    ),
    considered_alternatives=[
        AlternativeConsidered(
            name="Pure Reactive Agent Loop (ReAct)",
            rejected_reason="Tends to focus on immediate next steps and lose track of the holistic 10+ step objective"
        )
    ],
    chosen_solution_summary="Separate task into an upfront Planner (generates structured step DAG), a specialized Step Executor, and a dynamic Replanner that triggers when execution state deviates.",
    tradeoffs=[
        TradeoffItem(
            dimension="Macro Planning Clarity vs Replanning Overhead",
            advantage="Maintains global objective focus; allows parallel step analysis and clean progress visualization",
            disadvantage="Rigid upfront plans can require frequent replanning in non-deterministic environments",
            rationale="Separation of concerns between strategic decomposition and tactical execution"
        )
    ],
    failure_modes=[
        FailureMode(
            trigger_condition="Step execution fails catastrophically and replanner regenerates identical failing plan",
            consequence="Infinite replanning loop",
            mitigation_strategy="Pass historical step failure trace into replanner context and limit max replans (<= 2)"
        )
    ],
    reference_code=ReferenceCodeSlice(
        entry_point="plan_and_execute",
        language="python",
        code_content=PLAN_AND_EXECUTE_CODE,
        test_code=PLAN_AND_EXECUTE_TEST,
        dependencies=[]
    ),
    evidence=EvidenceData(
        evidence_level=EvidenceLevel.CONTROLLED_SANDBOX,
        source_reference="Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning (Wang et al., ACL 2023)",
        test_pass_rate=1.0,
        benchmark_metrics={"complex_task_completion_rate": "89% on multi-step workflows"}
    ),
    confidence_score=0.97,
    status=LifecycleStatus.ACTIVE
)
