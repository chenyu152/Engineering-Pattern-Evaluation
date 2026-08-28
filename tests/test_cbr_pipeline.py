import pytest
from storage.hybrid_repository import HybridRepository
from seeds.loader import seed_database
from engine.cbr_orchestrator import CBROrchestrator

def test_cbr_orchestrator_agent_workflow():
    repo = HybridRepository()
    seed_database(repo)
    orchestrator = CBROrchestrator(repository=repo)

    query = "Orchestrator-Workers: 需要将复杂的任务并行分解给多个 Worker 并汇总结果"
    report = orchestrator.process_task(query, auto_verify_sandbox=True)

    assert report.selected_pattern_id == "agent_orchestrator_workers_anthropic"
    assert len(report.top_candidates) > 0
    assert report.top_candidates[0].recommendation_verdict == "STRONGLY_RECOMMENDED"
    assert "Orchestrator-Workers" in report.decision_rationale

def test_cbr_orchestrator_redis_queue():
    repo = HybridRepository()
    seed_database(repo)
    orchestrator = CBROrchestrator(repository=repo)

    query = "Redis Stream 消息队列: 给订单微服务设计异步任务队列，需要消费组与低延迟"
    report = orchestrator.process_task(query, auto_verify_sandbox=True)

    assert report.selected_pattern_id == "backend_redis_stream_queue"
    assert "Redis Stream" in report.decision_rationale
