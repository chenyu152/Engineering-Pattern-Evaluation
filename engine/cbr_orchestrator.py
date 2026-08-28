import logging
from typing import Optional, Dict, Any
from core.schema import CBRDecisionReport, DecisionSlice, ReferenceCodeSlice
from storage.hybrid_repository import HybridRepository
from evaluator.sandbox_runner import SandboxRunner
from .task_analyzer import TaskAnalyzer
from .pattern_retriever import PatternRetriever
from .tradeoff_advisor import TradeoffAdvisor
from .adaptation_agent import AdaptationAgent

logger = logging.getLogger(__name__)

class CBROrchestrator:
    """
    End-to-End CBR (Case-Based Reasoning) Orchestrator:
    1. Retrieve: Analyzes query & performs hybrid search over verified Decision Slices.
    2. Advise/Select: Generates Trade-off Comparison matrix & selects optimal pattern.
    3. Adapt (Revise): Mutates and adapts verified reference code to user's domain.
    4. Verify: Runs sandbox verification.
    5. Retain: Feedback loops into evidence graph.
    """
    def __init__(self, repository: Optional[HybridRepository] = None, sandbox: Optional[SandboxRunner] = None):
        self.repository = repository or HybridRepository()
        self.sandbox = sandbox or SandboxRunner()
        self.analyzer = TaskAnalyzer()
        self.retriever = PatternRetriever(self.repository)
        self.advisor = TradeoffAdvisor()
        self.adapter = AdaptationAgent()

    def process_task(self, query: str, auto_verify_sandbox: bool = True) -> CBRDecisionReport:
        # Step 1: Task analysis
        task_analysis = self.analyzer.analyze(query)

        # Step 2: Retrieve candidate patterns
        candidates = self.retriever.retrieve(task_analysis, top_k=3)

        if not candidates:
            # Fallback if repository is empty or no match
            raise ValueError(f"No matching engineering patterns found in repository for query: '{query}'")

        # Step 3: Evaluate trade-offs
        tradeoff_comparisons = self.advisor.evaluate_candidates(task_analysis, candidates)

        # Step 4: Pick best candidate
        best_match = candidates[0]
        selected_slice: DecisionSlice = best_match["slice"]

        # Step 5: Adapt reference code slice
        adaptation_res = self.adapter.adapt_reference_slice(selected_slice, task_analysis)

        # Step 6: Optional Sandbox verification
        sandbox_warning = None
        if auto_verify_sandbox:
            test_slice = ReferenceCodeSlice(
                entry_point=adaptation_res["entry_point"],
                language="python",
                code_content=adaptation_res["adapted_code"],
                test_code=adaptation_res["adapted_test"],
                dependencies=adaptation_res["dependencies"]
            )
            sandbox_res = self.sandbox.run_code_slice_test(test_slice)
            if not sandbox_res.get("success", False):
                sandbox_warning = f"Sandbox verification warning: {sandbox_res.get('error')}"

        rationale = (
            f"Selected '{selected_slice.pattern_name}' (Standard: {selected_slice.standard_reference.value}) "
            f"with suitability score {best_match['composite_score']:.2f}. "
            f"This architecture best resolves '{selected_slice.problem_statement}' while satisfying "
            f"the requested constraints."
        )

        return CBRDecisionReport(
            task_analysis=task_analysis,
            top_candidates=tradeoff_comparisons,
            selected_pattern_id=selected_slice.id,
            decision_rationale=rationale,
            reference_code_slice=selected_slice.reference_code,
            adaptation_instructions=adaptation_res["instructions"],
            suggested_test_strategy=(
                f"Execute isolated unit tests and benchmark throughput against failure mode guardrails: "
                + "; ".join([f.mitigation_strategy for f in selected_slice.failure_modes])
            ),
            lifecycle_warning=sandbox_warning
        )
