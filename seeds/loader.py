import logging
from typing import List
from core.schema import DecisionSlice
from storage.hybrid_repository import HybridRepository

# Agent Patterns
from seeds.agent_patterns.evaluator_optimizer import SEED_EVALUATOR_OPTIMIZER
from seeds.agent_patterns.router import SEED_ROUTER
from seeds.agent_patterns.orchestrator_workers import SEED_ORCHESTRATOR_WORKERS
from seeds.agent_patterns.react_loop import SEED_REACT_LOOP
from seeds.agent_patterns.plan_and_execute import SEED_PLAN_AND_EXECUTE
from seeds.agent_patterns.rag_hybrid_search import SEED_RAG_HYBRID_SEARCH

# Backend & Distributed Patterns
from seeds.backend_patterns.redis_stream_queue import SEED_REDIS_STREAM
from seeds.backend_patterns.cache_aside import SEED_CACHE_ASIDE
from seeds.backend_patterns.distributed_lock_redis import SEED_REDIS_DISTRIBUTED_LOCK
from seeds.backend_patterns.rate_limiter_token_bucket import SEED_RATE_LIMITER_TOKEN_BUCKET
from seeds.backend_patterns.circuit_breaker import SEED_CIRCUIT_BREAKER
from seeds.backend_patterns.idempotent_consumer import SEED_IDEMPOTENT_CONSUMER
from seeds.backend_patterns.saga_orchestrator import SEED_SAGA_ORCHESTRATOR

logger = logging.getLogger(__name__)

GOLDEN_SEEDS: List[DecisionSlice] = [
    # Agentic workflows (Anthropic / Google Research standards)
    SEED_EVALUATOR_OPTIMIZER,
    SEED_ROUTER,
    SEED_ORCHESTRATOR_WORKERS,
    SEED_REACT_LOOP,
    SEED_PLAN_AND_EXECUTE,
    SEED_RAG_HYBRID_SEARCH,

    # Backend, Distributed & Resilience patterns (MADR standards)
    SEED_REDIS_STREAM,
    SEED_CACHE_ASIDE,
    SEED_REDIS_DISTRIBUTED_LOCK,
    SEED_RATE_LIMITER_TOKEN_BUCKET,
    SEED_CIRCUIT_BREAKER,
    SEED_IDEMPOTENT_CONSUMER,
    SEED_SAGA_ORCHESTRATOR,
]

def seed_database(repository: HybridRepository) -> int:
    """Seeds all golden authoritative decision slices into storage."""
    count = 0
    for seed in GOLDEN_SEEDS:
        repository.save_decision_slice(seed)
        count += 1
    logger.info(f"Seeded {count} authoritative golden decision slices into repository.")
    return count

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    repo = HybridRepository()
    n = seed_database(repo)
    print(f"Successfully loaded {n} golden seeds into HybridRepository!")
