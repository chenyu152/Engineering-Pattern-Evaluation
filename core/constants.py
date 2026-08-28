from enum import Enum

class EvidenceLevel(str, Enum):
    """
    Three-tier evidence pyramid:
    L1 (OBSERVED): Solution observed in popular production repositories / official repos.
    L2 (COMPARATIVE): Documented post-mortem or comparative migration history (e.g. A migrated to B).
    L3 (CONTROLLED_SANDBOX): Verified with reproducible test suite and benchmark in isolated sandbox.
    """
    OBSERVED = "Observed"
    COMPARATIVE = "Comparative"
    CONTROLLED_SANDBOX = "Controlled_Sandbox"

class PatternCategory(str, Enum):
    AGENTIC_WORKFLOW = "Agentic_Workflow"       # Anthropic 5 workflow patterns (Prompt Chaining, Router, Evaluator-Optimizer...)
    AGENTIC_MULTI_AGENT = "Agentic_Multi_Agent" # Orchestrator-Workers, Autonomous Swarm
    BACKEND_DISTRIBUTED = "Backend_Distributed" # Distributed Locking, Message Queues, Event Sourcing, CQRS
    DATA_PERSISTENCE = "Data_Persistence"       # Cache-Aside, Write-Behind, Vector RAG Indexing
    FAULT_TOLERANCE = "Fault_Tolerance"         # Circuit Breaker, Exponential Retry with Jitter, Bulkhead
    TESTING_VERIFICATION = "Testing_Verification" # Property-Based Testing, HIL Simulation, Contract Test

class StandardReference(str, Enum):
    ANTHROPIC_AGENTIC = "Anthropic: Building Effective Agents"
    MADR_SPEC = "MADR (Markdown Any Architecture Decision Records) v3.0"
    VOYAGER_SKILL = "Voyager Executable Skill Standard"
    REFLEXION_MEMORY = "Reflexion Verbal RL & Memory Standard"
    SWE_BENCH = "SWE-bench Industrial Trajectory Format"

class LifecycleStatus(str, Enum):
    ACTIVE = "Active"
    STALE = "Stale"
    DEPRECATED = "Deprecated"
