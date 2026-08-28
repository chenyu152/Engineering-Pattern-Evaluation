import pytest
from storage.vector_store import VectorStore
from storage.evidence_graph import EvidenceGraph
from storage.hybrid_repository import HybridRepository
from seeds.loader import seed_database
from engine.task_analyzer import TaskAnalyzer

def test_hybrid_retrieval():
    repo = HybridRepository()
    seed_database(repo)

    analyzer = TaskAnalyzer()
    task = analyzer.analyze("我们需要实现一个基于 LLM 的代码评审系统，需要对初稿进行评估并根据反馈多轮迭代优化")
    
    results = repo.hybrid_search(task, top_k=3)
    assert len(results) > 0
    top_match = results[0]["slice"]
    # Evaluator-Optimizer should be the top match for iterative evaluation loop
    assert "Evaluator-Optimizer" in top_match.pattern_name
