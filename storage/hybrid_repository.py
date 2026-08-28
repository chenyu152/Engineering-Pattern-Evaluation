import logging
from typing import List, Dict, Any, Optional
from core.schema import DecisionSlice, TaskAnalysisResult
from .vector_store import VectorStore
from .evidence_graph import EvidenceGraph

logger = logging.getLogger(__name__)

class HybridRepository:
    """
    Unified storage facade combining semantic vector search (ChromaDB/TF-IDF) 
    with relational constraint filtering (NetworkX Evidence Graph).
    """
    def __init__(self, vector_store: Optional[VectorStore] = None, evidence_graph: Optional[EvidenceGraph] = None):
        self.vector_store = vector_store or VectorStore()
        self.evidence_graph = evidence_graph or EvidenceGraph()
        self._memory_cache: Dict[str, DecisionSlice] = {}
        self._bootstrap_vector_index()

    def _bootstrap_vector_index(self):
        """Loads all existing patterns from evidence graph into vector store for indexing."""
        all_patterns = self.list_all()
        for p in all_patterns:
            self._memory_cache[p.id] = p
            self.vector_store.upsert_slice(p)

    def save_decision_slice(self, decision: DecisionSlice):
        """Atomically saves to both Vector Store and Evidence Graph."""
        self._memory_cache[decision.id] = decision
        self.vector_store.upsert_slice(decision)
        self.evidence_graph.add_decision_slice(decision)
        self.evidence_graph.save_graph()
        logger.info(f"Successfully stored DecisionSlice: {decision.id} ({decision.pattern_name})")

    def get_by_id(self, slice_id: str) -> Optional[DecisionSlice]:
        if slice_id in self._memory_cache:
            return self._memory_cache[slice_id]
        raw = self.evidence_graph.get_pattern_by_id(slice_id)
        if raw:
            slice_obj = DecisionSlice(**raw)
            self._memory_cache[slice_id] = slice_obj
            return slice_obj
        return None

    def list_all(self) -> List[DecisionSlice]:
        results = []
        for node_id, data in self.evidence_graph.graph.nodes(data=True):
            if data.get("node_type") == "Pattern":
                raw = data.get("raw_data")
                if raw:
                    results.append(DecisionSlice(**raw))
        return results

    def hybrid_search(
        self,
        task_analysis: TaskAnalysisResult,
        top_k: int = 3,
        min_confidence: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Executes dual-channel retrieval:
        1. Graph filter: filters out candidate IDs that violate hard constraints.
        2. Vector search: ranks candidates based on semantic relevance to the task query.
        3. Returns combined scored candidates.
        """
        # Ensure index is synced
        if not self.vector_store._docs and self.evidence_graph.graph.number_of_nodes() > 0:
            self._bootstrap_vector_index()

        # Step 1: Constraint-based graph filtering
        graph_valid_ids = self.evidence_graph.filter_patterns_by_constraints(
            min_confidence=min_confidence
        )

        # Step 2: Vector semantic search
        vector_matches = self.vector_store.query_similar(
            query=task_analysis.raw_query,
            top_k=top_k * 3
        )

        scored_candidates = []
        for match in vector_matches:
            doc_id = match["id"]
            if graph_valid_ids and doc_id not in graph_valid_ids:
                continue
            
            slice_obj = self.get_by_id(doc_id)
            if not slice_obj:
                continue

            similarity = match["similarity"]
            composite_score = 0.65 * similarity + 0.35 * slice_obj.confidence_score

            scored_candidates.append({
                "slice": slice_obj,
                "semantic_similarity": similarity,
                "composite_score": composite_score
            })

        # If empty, provide category or general fallback
        if not scored_candidates:
            all_patterns = self.list_all()
            for p in all_patterns:
                sim = 0.6 if p.category == task_analysis.inferred_category else 0.4
                scored_candidates.append({
                    "slice": p,
                    "semantic_similarity": sim,
                    "composite_score": 0.65 * sim + 0.35 * p.confidence_score
                })

        # Sort by composite score descending
        scored_candidates.sort(key=lambda x: x["composite_score"], reverse=True)
        return scored_candidates[:top_k]
