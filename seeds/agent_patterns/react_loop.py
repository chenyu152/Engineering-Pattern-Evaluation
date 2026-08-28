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

REACT_CODE = '''
from typing import Dict, Any, List, Callable, Optional

def react_agent_loop(
    user_goal: str,
    reason_fn: Callable[[str, List[Dict[str, Any]]], Dict[str, Any]],
    tool_executor_fn: Callable[[str, Dict[str, Any]], Any],
    max_steps: int = 5
) -> Dict[str, Any]:
    """
    ReAct (Reason + Act + Observation) Loop Pattern.
    Interleaves reasoning traces and tool actions in a tight loop until the goal is achieved or terminated.
    """
    trajectory: List[Dict[str, Any]] = []
    
    for step in range(1, max_steps + 1):
        # 1. Thought & Action Decision
        decision = reason_fn(user_goal, trajectory)
        thought = decision.get("thought", "")
        action_name = decision.get("action")
        action_args = decision.get("args", {})
        
        # Check if agent decided to finish
        if action_name == "finish" or not action_name:
            final_answer = decision.get("final_answer", thought)
            trajectory.append({"step": step, "thought": thought, "action": "finish", "observation": "Goal achieved"})
            return {
                "status": "success",
                "total_steps": step,
                "final_answer": final_answer,
                "trajectory": trajectory
            }
        
        # 2. Execute Action (Tool Calling)
        try:
            observation = tool_executor_fn(action_name, action_args)
        except Exception as e:
            observation = f"Tool Execution Error: {str(e)}"
        
        trajectory.append({
            "step": step,
            "thought": thought,
            "action": action_name,
            "args": action_args,
            "observation": observation
        })
        
    return {
        "status": "max_steps_exceeded",
        "total_steps": max_steps,
        "final_answer": "Terminated due to step limit",
        "trajectory": trajectory
    }
'''

REACT_TEST = '''
def test_react_agent_loop():
    # Mock reason function: Step 1 calls calculator, Step 2 finishes
    def mock_reason(goal: str, trajectory):
        if len(trajectory) == 0:
            return {"thought": "I need to calculate 25 * 4", "action": "calculator", "args": {"expr": "25*4"}}
        else:
            obs = trajectory[0]["observation"]
            return {"thought": f"The answer is {obs}", "action": "finish", "final_answer": f"Result is {obs}"}

    def mock_tool(name: str, args: dict):
        if name == "calculator":
            return eval(args["expr"])
        return "Unknown tool"

    res = react_agent_loop("What is 25 * 4?", mock_reason, mock_tool, max_steps=4)
    assert res["status"] == "success"
    assert res["total_steps"] == 2
    assert res["final_answer"] == "Result is 100"
    assert len(res["trajectory"]) == 2
'''

SEED_REACT_LOOP = DecisionSlice(
    id="agent_react_loop_standard",
    pattern_name="ReAct (Reason + Act) Agent Loop",
    category=PatternCategory.AGENTIC_WORKFLOW,
    standard_reference=StandardReference.ANTHROPIC_AGENTIC,
    problem_statement="Single-shot prompt execution cannot solve dynamic tasks that require environmental exploration, interactive tool use, and step-by-step reasoning feedback.",
    context_constraints=ConstraintProfile(
        latency_budget_ms=500.0,
        token_cost_sensitivity="medium",
        scale="single-node",
        infra_dependencies=[]
    ),
    considered_alternatives=[
        AlternativeConsidered(
            name="Plan-and-Solve (Static Sequential Planning)",
            rejected_reason="Cannot adapt when intermediate tool execution encounters unexpected errors or dynamic outputs"
        ),
        AlternativeConsidered(
            name="Direct Tool Calling without Explicit Thought Trace",
            rejected_reason="Significantly higher error rate in multi-step parameter generation"
        )
    ],
    chosen_solution_summary="Interleave explicit Thought reasoning generation, Tool Action invocation, and Environment Observation feedback in an iterative loop until completion.",
    tradeoffs=[
        TradeoffItem(
            dimension="Exploration Adaptability vs Token & Latency Overhead",
            advantage="Dynamic adaptation to real-time tool observations; self-correcting on tool errors",
            disadvantage="Linear accumulation of token context and wall-clock latency per step",
            rationale="Dynamic reasoning requires observing intermediate tool state before deciding the next step"
        )
    ],
    failure_modes=[
        FailureMode(
            trigger_condition="Tool returns repetitive observation without progress",
            consequence="Infinite thought-action loop consuming token budget",
            mitigation_strategy="Enforce hard max_steps cap and repetitive action detection guardrails"
        )
    ],
    reference_code=ReferenceCodeSlice(
        entry_point="react_agent_loop",
        language="python",
        code_content=REACT_CODE,
        test_code=REACT_TEST,
        dependencies=[]
    ),
    evidence=EvidenceData(
        evidence_level=EvidenceLevel.CONTROLLED_SANDBOX,
        source_reference="ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al. / Google Research)",
        test_pass_rate=1.0,
        benchmark_metrics={"hotpot_qa_accuracy": "34% higher than direct prompting"}
    ),
    confidence_score=0.98,
    status=LifecycleStatus.ACTIVE
)
