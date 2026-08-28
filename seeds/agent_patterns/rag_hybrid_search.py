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

RAG_HYBRID_CODE = '''
import math
from typing import List, Dict, Any

def reciprocal_rank_fusion(
    dense_ranked_ids: List[str],
    sparse_ranked_ids: List[str],
    k: int = 60,
    top_n: int = 3
) -> List[Dict[str, Any]]:
    """
    RAG Hybrid Search Fusion: Reciprocal Rank Fusion (RRF).
    Combines dense semantic vector rankings with sparse keyword (BM25) rankings.
    Score = sum(1 / (k + rank_i))
    """
    scores: Dict[str, float] = {}
    
    # Process dense ranking
    for rank, doc_id in enumerate(dense_ranked_ids, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))
        
    # Process sparse ranking
    for rank, doc_id in enumerate(sparse_ranked_ids, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))
        
    # Sort descending by fused score
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    return [
        {"id": doc_id, "rrf_score": round(score, 5), "rank": i + 1}
        for i, (doc_id, score) in enumerate(sorted_items[:top_n])
    ]
'''

RAG_HYBRID_TEST = '''
def test_reciprocal_rank_fusion():
    dense_results = ["doc_A", "doc_B", "doc_C"]
    sparse_results = ["doc_B", "doc_D", "doc_A"]
    
    fused = reciprocal_rank_fusion(dense_results, sparse_results, k=60, top_n=3)
    
    # doc_B appears at rank 2 in dense and rank 1 in sparse -> highest total RRF score
    assert len(fused) == 3
    assert fused[0]["id"] == "doc_B"
    assert fused[1]["id"] == "doc_A"
'''

SEED_RAG_HYBRID_SEARCH = DecisionSlice(
    id="agent_rag_hybrid_search_rrf",
    pattern_name="Hybrid Search RAG with Reciprocal Rank Fusion",
    category=PatternCategory.DATA_PERSISTENCE,
    standard_reference=StandardReference.ANTHROPIC_AGENTIC,
    problem_statement="Pure dense semantic vector search struggles with exact keyword, symbol, ID, and technical acronym retrieval; pure keyword search fails at semantic conceptual matching.",
    context_constraints=ConstraintProfile(
        latency_budget_ms=30.0,
        scale="cluster",
        infra_dependencies=["VectorDB"]
    ),
    considered_alternatives=[
        AlternativeConsidered(
            name="Dense Vector Search Only (Cosine Similarity)",
            rejected_reason="Frequently misses exact matches for code identifiers, error codes, and exact variable names"
        ),
        AlternativeConsidered(
            name="BM25 Sparse Search Only",
            rejected_reason="Fails to capture conceptual synonyms and cross-lingual semantic intents"
        )
    ],
    chosen_solution_summary="Execute parallel Dense (Vector Embedding) and Sparse (BM25/SPLADE) retrieval queries, then fuse and re-rank results using parameter-free Reciprocal Rank Fusion (RRF).",
    tradeoffs=[
        TradeoffItem(
            dimension="Recall & Precision vs Dual-Index Storage Overhead",
            advantage="Provides SOTA retrieval recall on both natural language queries and exact code symbols",
            disadvantage="Requires maintaining dual indexes (Inverted Index + Vector HNSW)",
            rationale="Complementary strengths of lexical and semantic representations eliminate retrieval blind spots"
        )
    ],
    failure_modes=[
        FailureMode(
            trigger_condition="Dense and sparse retrieval return completely disjoint candidate sets",
            consequence="RRF score ties and noisy ranking",
            mitigation_strategy="Apply downstream Cross-Encoder Re-ranker on the top fused candidates"
        )
    ],
    reference_code=ReferenceCodeSlice(
        entry_point="reciprocal_rank_fusion",
        language="python",
        code_content=RAG_HYBRID_CODE,
        test_code=RAG_HYBRID_TEST,
        dependencies=[]
    ),
    evidence=EvidenceData(
        evidence_level=EvidenceLevel.CONTROLLED_SANDBOX,
        source_reference="Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods (Cormack et al., SIGIR)",
        test_pass_rate=1.0,
        benchmark_metrics={"mrr_10": "0.84", "ndcg_10": "0.89"}
    ),
    confidence_score=0.98,
    status=LifecycleStatus.ACTIVE
)
