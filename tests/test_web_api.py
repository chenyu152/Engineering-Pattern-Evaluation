from fastapi.testclient import TestClient
from web.app import app

client = TestClient(app)

def test_api_overview():
    res = client.get("/api/overview")
    assert res.status_code == 200
    data = res.json()
    assert "total_patterns" in data
    assert data["total_patterns"] >= 13
    assert "evidence_distribution" in data

def test_api_patterns_list():
    res = client.get("/api/patterns")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 13

def test_api_evaluate():
    res = client.post("/api/evaluate", json={"query": "我们需要构建一个经典的 ReAct 推理行动循环 Agent"})
    assert res.status_code == 200
    data = res.json()
    assert "top_candidates" in data
    assert len(data["top_candidates"]) > 0

def test_api_graph_data():
    res = client.get("/api/graph")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0
