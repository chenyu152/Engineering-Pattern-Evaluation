import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from storage.hybrid_repository import HybridRepository
from seeds.loader import seed_database
from engine.cbr_orchestrator import CBROrchestrator
from evaluator.sandbox_runner import SandboxRunner
from evaluator.evidence_scorer import EvidenceScorer
from evaluator.stale_detector import StaleDetector
from ingestion.github_miner import RepositoryMiner

app = FastAPI(
    title="Engineering Pattern Evaluation & Decision Engine API",
    version="1.0.0",
    description="REST API for Engineering Decision Slices, CBR Architecture Evaluation, and Evidence Graph"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Repository & Engine instances
repo = HybridRepository()
if not repo.list_all():
    seed_database(repo)

orchestrator = CBROrchestrator(repository=repo)
sandbox = SandboxRunner()
scorer = EvidenceScorer()
detector = StaleDetector(repository=repo, sandbox=sandbox, scorer=scorer)
miner = RepositoryMiner(repository=repo, sandbox=sandbox)

# Request / Response Schemas
class EvaluateRequest(BaseModel):
    query: str

class SolveRequest(BaseModel):
    query: str
    output_dir: Optional[str] = None

class MineRequest(BaseModel):
    directory_path: str

@app.get("/api/overview")
def get_overview():
    patterns = repo.list_all()
    
    # Evidence level counts
    evidence_dist = {}
    category_dist = {}
    status_dist = {}
    
    for p in patterns:
        el = p.evidence.evidence_level.value
        evidence_dist[el] = evidence_dist.get(el, 0) + 1
        
        cat = p.category.value
        category_dist[cat] = category_dist.get(cat, 0) + 1
        
        st = p.status.value
        status_dist[st] = status_dist.get(st, 0) + 1

    return {
        "total_patterns": len(patterns),
        "evidence_distribution": evidence_dist,
        "category_distribution": category_dist,
        "status_distribution": status_dist,
        "graph_node_count": repo.evidence_graph.graph.number_of_nodes(),
        "graph_edge_count": repo.evidence_graph.graph.number_of_edges()
    }

@app.get("/api/patterns")
def list_patterns(
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    patterns = repo.list_all()
    filtered = []
    for p in patterns:
        if category and p.category.value != category:
            continue
        if status and p.status.value != status:
            continue
        if search:
            q = search.lower()
            if q not in p.pattern_name.lower() and q not in p.problem_statement.lower() and q not in p.id.lower():
                continue
        filtered.append(p.model_dump())
    return {"count": len(filtered), "patterns": filtered}

@app.get("/api/patterns/{slice_id}")
def get_pattern_detail(slice_id: str):
    p = repo.get_by_id(slice_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return p.model_dump()

@app.post("/api/evaluate")
def evaluate_task(req: EvaluateRequest):
    try:
        report = orchestrator.process_task(req.query, auto_verify_sandbox=False)
        return report.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve")
def solve_task(req: SolveRequest):
    try:
        report = orchestrator.process_task(req.query, auto_verify_sandbox=True)
        decision_slice = repo.get_by_id(report.selected_pattern_id)
        adaptation_res = orchestrator.adapter.adapt_reference_slice(decision_slice, report.task_analysis)
        
        result_payload = {
            "report": report.model_dump(),
            "solution_code": adaptation_res["adapted_code"],
            "test_code": adaptation_res["adapted_test"],
            "instructions": adaptation_res["instructions"],
            "adr_summary": f"# ADR: {decision_slice.pattern_name}\n\n{report.decision_rationale}"
        }

        if req.output_dir:
            out_path = Path(req.output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            with open(out_path / "solution.py", "w", encoding="utf-8") as f:
                f.write(adaptation_res["adapted_code"])
            with open(out_path / "test_solution.py", "w", encoding="utf-8") as f:
                f.write(adaptation_res["adapted_test"])
            with open(out_path / "ARCHITECTURE_DECISION.md", "w", encoding="utf-8") as f:
                f.write(result_payload["adr_summary"])
            result_payload["saved_to"] = str(out_path)

        return result_payload
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/graph")
def get_graph_data():
    """Returns nodes and edges formatted for Vis.js Network graph visualization."""
    g = repo.evidence_graph.graph
    nodes = []
    edges = []

    # Styling mapping for node types
    type_styles = {
        "Pattern": {"shape": "box", "color": {"background": "#3b82f6", "border": "#1d4ed8"}, "font": {"color": "#ffffff", "face": "system-ui"}},
        "Category": {"shape": "ellipse", "color": {"background": "#8b5cf6", "border": "#6d28d9"}, "font": {"color": "#ffffff"}},
        "Standard": {"shape": "diamond", "color": {"background": "#10b981", "border": "#047857"}, "font": {"color": "#ffffff"}},
        "InfraDependency": {"shape": "hexagon", "color": {"background": "#f59e0b", "border": "#b45309"}, "font": {"color": "#ffffff"}},
        "FailureMode": {"shape": "triangle", "color": {"background": "#ef4444", "border": "#b91c1c"}, "font": {"color": "#ffffff"}},
        "Alternative": {"shape": "dot", "color": {"background": "#6b7280", "border": "#4b5563"}, "font": {"color": "#ffffff"}}
    }

    for node_id, data in g.nodes(data=True):
        ntype = data.get("node_type", "Pattern")
        style = type_styles.get(ntype, type_styles["Pattern"])
        
        label = data.get("pattern_name") or data.get("name") or data.get("trigger") or node_id.split(":")[-1]
        # Truncate label if too long
        if len(label) > 30:
            label = label[:27] + "..."

        nodes.append({
            "id": node_id,
            "label": f"[{ntype}]\n{label}",
            "title": f"<b>Type:</b> {ntype}<br/><b>ID:</b> {node_id}<br/>" + "<br/>".join([f"<b>{k}:</b> {v}" for k, v in data.items() if k not in ["raw_data"]]),
            "node_type": ntype,
            **style
        })

    for src, dst, data in g.edges(data=True):
        etype = data.get("edge_type", "RELATED_TO")
        edges.append({
            "from": src,
            "to": dst,
            "label": etype,
            "arrows": "to",
            "font": {"size": 10, "color": "#9ca3af", "align": "middle"},
            "color": {"color": "#4b5563", "highlight": "#60a5fa"}
        })

    return {"nodes": nodes, "edges": edges}

@app.post("/api/audit")
def audit_all_patterns():
    results = detector.audit_all_patterns()
    return {"audit_count": len(results), "results": results}

@app.post("/api/mine")
def mine_repository(req: MineRequest):
    try:
        res = miner.mine_directory(req.directory_path)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mount static frontend files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
