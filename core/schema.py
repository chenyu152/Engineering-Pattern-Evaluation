from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from .constants import EvidenceLevel, PatternCategory, StandardReference, LifecycleStatus

class ConstraintProfile(BaseModel):
    """Execution context and constraints required or assumed by the pattern"""
    throughput: Optional[str] = Field(None, description="e.g. '< 10000 QPS' or '> 100k QPS'")
    latency_budget_ms: Optional[float] = Field(None, description="P99 latency expectation in milliseconds")
    consistency_level: Optional[str] = Field(None, description="e.g. 'eventual', 'strong', 'read-your-writes'")
    scale: Optional[str] = Field(None, description="e.g. 'single-node', 'cluster', 'edge-embedded'")
    infra_dependencies: List[str] = Field(default_factory=list, description="Required infra (e.g. ['Redis', 'PostgreSQL'])")
    token_cost_sensitivity: Optional[Literal["low", "medium", "high"]] = Field("medium", description="Agent token budget sensitivity")

class TradeoffItem(BaseModel):
    """Structured architectural trade-off dimension"""
    dimension: str = Field(..., description="e.g. 'Latency vs Cost', 'Complexity vs Maintainability'")
    advantage: str = Field(..., description="Positive gains")
    disadvantage: str = Field(..., description="Trade-off cost / drawbacks")
    rationale: str = Field(..., description="Why this trade-off exists in engineering practice")

class AlternativeConsidered(BaseModel):
    """Other candidates evaluated and why they were rejected or subordinated"""
    name: str = Field(..., description="Candidate name (e.g. 'Kafka', 'Multi-Agent Autonomous Swarm')")
    rejected_reason: str = Field(..., description="Engineering rationale for rejection under given constraints")

class FailureMode(BaseModel):
    """Failure boundary and mitigation (Reflexion pattern memory)"""
    trigger_condition: str = Field(..., description="Scenario causing the architecture to fail")
    consequence: str = Field(..., description="System symptom (e.g. OOM, Deadlock, Infinite LLM Loop)")
    mitigation_strategy: str = Field(..., description="How to prevent or guard against this failure")

class ReferenceCodeSlice(BaseModel):
    """Minimal executable, tested code slice (Voyager style)"""
    entry_point: str = Field(..., description="Function/Class entry name")
    language: str = Field(default="python", description="Language (python, typescript, go, rust)")
    code_content: str = Field(..., description="Clean, standalone implementation code")
    test_code: str = Field(..., description="Runnable pytest / unit test suite for this slice")
    dependencies: List[str] = Field(default_factory=list, description="Required libraries with versions")

class EvidenceData(BaseModel):
    """Quantifiable evidence for pattern validity"""
    evidence_level: EvidenceLevel = Field(default=EvidenceLevel.OBSERVED)
    verified_runtime_version: Optional[str] = Field(None, description="Tested language/runtime version")
    test_pass_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    benchmark_metrics: Dict[str, Any] = Field(default_factory=dict, description="e.g. {'qps': 12000, 'p99_ms': 3.1}")
    source_reference: str = Field(..., description="Origin repo, paper DOI, or official guide")
    last_verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))

class DecisionSlice(BaseModel):
    """
    Core Machine-Readable ADR (MADR) and Engineering Decision Slice
    Represents an atomic, verified engineering solution with trade-offs and executable code.
    """
    id: str = Field(..., description="Unique slug identifier (e.g. 'agent_evaluator_optimizer_01')")
    pattern_name: str = Field(..., description="Standard pattern name")
    category: PatternCategory = Field(..., description="Domain category")
    standard_reference: StandardReference = Field(..., description="Authoritative reference standard")
    problem_statement: str = Field(..., description="The core technical problem this solves")
    context_constraints: ConstraintProfile = Field(default_factory=ConstraintProfile)
    considered_alternatives: List[AlternativeConsidered] = Field(default_factory=list)
    chosen_solution_summary: str = Field(..., description="High-level solution architecture")
    tradeoffs: List[TradeoffItem] = Field(default_factory=list)
    failure_modes: List[FailureMode] = Field(default_factory=list)
    reference_code: ReferenceCodeSlice
    evidence: EvidenceData
    confidence_score: float = Field(default=0.9, ge=0.0, le=1.0)
    status: LifecycleStatus = Field(default=LifecycleStatus.ACTIVE)

class TaskAnalysisResult(BaseModel):
    """Parsed output of user's task request"""
    raw_query: str
    inferred_category: PatternCategory
    extracted_constraints: ConstraintProfile
    key_requirements: List[str]
    potential_risks: List[str]

class TradeoffComparison(BaseModel):
    """Comparison matrix among candidate patterns"""
    candidate_id: str
    pattern_name: str
    suitability_score: float
    pros: List[str]
    cons: List[str]
    critical_failure_risks: List[str]
    recommendation_verdict: Literal["STRONGLY_RECOMMENDED", "VIABLE_ALTERNATIVE", "NOT_RECOMMENDED"]

class CBRDecisionReport(BaseModel):
    """Comprehensive CBR decision response for Coding Agent"""
    task_analysis: TaskAnalysisResult
    top_candidates: List[TradeoffComparison]
    selected_pattern_id: str
    decision_rationale: str
    reference_code_slice: ReferenceCodeSlice
    adaptation_instructions: str
    suggested_test_strategy: str
    lifecycle_warning: Optional[str] = None
