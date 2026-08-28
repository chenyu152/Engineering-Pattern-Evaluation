import re
from typing import List
from core.schema import TaskAnalysisResult, ConstraintProfile, PatternCategory

class TaskAnalyzer:
    """
    Analyzes raw user task query, extracts engineering constraints (scale, latency, dependencies, token budget)
    and infers the relevant architectural pattern category.
    """
    def __init__(self):
        pass

    def analyze(self, query: str) -> TaskAnalysisResult:
        lower_q = query.lower()

        # 1. Infer Category
        if any(k in lower_q for k in ["agent", "evaluator", "optimizer", "router", "prompt chain", "multi-agent", "orchestrator"]):
            if any(k in lower_q for k in ["multi-agent", "swarm", "orchestrator", "workers"]):
                category = PatternCategory.AGENTIC_MULTI_AGENT
            else:
                category = PatternCategory.AGENTIC_WORKFLOW
        elif any(k in lower_q for k in ["queue", "mq", "stream", "lock", "distributed", "event", "kafka", "redis", "rpc"]):
            category = PatternCategory.BACKEND_DISTRIBUTED
        elif any(k in lower_q for k in ["cache", "redis", "database", "postgres", "vector", "rag", "embedding"]):
            category = PatternCategory.DATA_PERSISTENCE
        elif any(k in lower_q for k in ["circuit", "retry", "fallback", "bulkhead", "rate limit"]):
            category = PatternCategory.FAULT_TOLERANCE
        elif any(k in lower_q for k in ["test", "mock", "hil", "benchmark", "verify"]):
            category = PatternCategory.TESTING_VERIFICATION
        else:
            category = PatternCategory.BACKEND_DISTRIBUTED

        # 2. Extract Constraints
        constraints = ConstraintProfile()

        # Check for infra keywords
        infras = []
        if "redis" in lower_q:
            infras.append("Redis")
        if "kafka" in lower_q:
            infras.append("Kafka")
        if "postgres" in lower_q or "postgresql" in lower_q:
            infras.append("PostgreSQL")
        if "sqlite" in lower_q:
            infras.append("SQLite")
        constraints.infra_dependencies = infras

        # Check scale & latency hints
        if any(k in lower_q for k in ["10万", "100k", "high throughput", "高并发", "qps"]):
            constraints.scale = "high-concurrency"
        elif any(k in lower_q for k in ["single", "embedded", "lightweight", "轻量"]):
            constraints.scale = "single-node"

        if any(k in lower_q for k in ["low latency", "低延迟", "实时", "real-time"]):
            constraints.latency_budget_ms = 50.0

        # Check token cost sensitivity
        if any(k in lower_q for k in ["low cost", "省token", "成本敏感", "token budget"]):
            constraints.token_cost_sensitivity = "high"

        # Key requirements & potential risks
        key_requirements = [
            f"Target domain: {category.value}",
            f"Infrastructural assumptions: {', '.join(infras) if infras else 'Zero mandatory infra'}"
        ]

        potential_risks = []
        if "redis" in lower_q and "queue" in lower_q:
            potential_risks.append("Risk of unmanaged Redis memory growth without MAXLEN eviction")
        if category in [PatternCategory.AGENTIC_WORKFLOW, PatternCategory.AGENTIC_MULTI_AGENT]:
            potential_risks.append("Risk of infinite LLM evaluation/optimizer loops or token budget blowup")

        return TaskAnalysisResult(
            raw_query=query,
            inferred_category=category,
            extracted_constraints=constraints,
            key_requirements=key_requirements,
            potential_risks=potential_risks
        )
