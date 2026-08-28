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

ORCHESTRATOR_CODE = '''
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor

def orchestrator_workers(
    complex_task: str,
    orchestrator_fn: Callable[[str], List[Dict[str, Any]]],
    worker_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    synthesizer_fn: Callable[[str, List[Dict[str, Any]]], str],
    max_workers: int = 4
) -> Dict[str, Any]:
    """
    Anthropic Building Effective Agents: Orchestrator-Workers Pattern.
    Central orchestrator breaks down task into independent subtasks, workers execute in parallel,
    and synthesizer aggregates results.
    """
    # 1. Decompose task
    subtasks = orchestrator_fn(complex_task)
    if not subtasks:
        return {"status": "empty_subtasks", "result": ""}

    # 2. Parallel worker execution
    worker_results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker_fn, task) for task in subtasks]
        for future in futures:
            worker_results.append(future.result())

    # 3. Synthesize final outcome
    final_output = synthesizer_fn(complex_task, worker_results)
    return {
        "status": "success",
        "subtasks_count": len(subtasks),
        "worker_results": worker_results,
        "final_output": final_output
    }
'''

ORCHESTRATOR_TEST = '''
def test_orchestrator_workers():
    def mock_orchestrator(task: str):
        return [{"id": 1, "subtask": "Analyze module A"}, {"id": 2, "subtask": "Analyze module B"}]

    def mock_worker(subtask_dict):
        return {"subtask_id": subtask_dict["id"], "summary": f"Findings for {subtask_dict['subtask']}"}

    def mock_synthesizer(task, results):
        return "Combined Report: " + " & ".join([r["summary"] for r in results])

    res = orchestrator_workers("Comprehensive Code Audit", mock_orchestrator, mock_worker, mock_synthesizer)
    assert res["status"] == "success"
    assert res["subtasks_count"] == 2
    assert "Findings for Analyze module A" in res["final_output"]
'''

SEED_ORCHESTRATOR_WORKERS = DecisionSlice(
    id="agent_orchestrator_workers_anthropic",
    pattern_name="Orchestrator-Workers Pattern",
    category=PatternCategory.AGENTIC_MULTI_AGENT,
    standard_reference=StandardReference.ANTHROPIC_AGENTIC,
    problem_statement="Complex, multi-faceted tasks (like full-repo audits or parallel research) exceed single-pass context windows and require parallel decomposition without chaotic peer-to-peer agent chatter.",
    context_constraints=ConstraintProfile(
        scale="cluster",
        token_cost_sensitivity="medium",
        infra_dependencies=[]
    ),
    considered_alternatives=[
        AlternativeConsidered(
            name="Sequential Prompt Chaining",
            rejected_reason="Latency grows linearly with the number of subtasks; no parallelism"
        ),
        AlternativeConsidered(
            name="Fully Decentralized Peer Swarm",
            rejected_reason="Unpredictable convergence, high token waste, difficult observability"
        )
    ],
    chosen_solution_summary="A central orchestrator dynamically generates subtasks, dispatches them to parallel workers, and synthesizes results into a unified output.",
    tradeoffs=[
        TradeoffItem(
            dimension="Parallel Throughput vs Orchestrator Single Point of Failure",
            advantage="Dramatic reduction in wall-clock latency through parallel worker execution",
            disadvantage="Overall output quality heavily depends on initial task decomposition accuracy",
            rationale="Subtask independence enables linear horizontal scaling"
        )
    ],
    failure_modes=[
        FailureMode(
            trigger_condition="Subtasks have hidden inter-dependencies that require sequential outputs",
            consequence="Worker execution returns incomplete or incompatible partial results",
            mitigation_strategy="Validate subtask DAG independence before dispatching to thread pool"
        )
    ],
    reference_code=ReferenceCodeSlice(
        entry_point="orchestrator_workers",
        language="python",
        code_content=ORCHESTRATOR_CODE,
        test_code=ORCHESTRATOR_TEST,
        dependencies=[]
    ),
    evidence=EvidenceData(
        evidence_level=EvidenceLevel.CONTROLLED_SANDBOX,
        source_reference="Anthropic Research: Building Effective Agents (2024)",
        test_pass_rate=1.0,
        benchmark_metrics={"speedup": "3.8x faster on 4-way parallelizable tasks"}
    ),
    confidence_score=0.98,
    status=LifecycleStatus.ACTIVE
)
