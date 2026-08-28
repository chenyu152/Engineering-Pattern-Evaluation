import json
import math
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from core.schema import DecisionSlice
from config.settings import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """
    High-performance, offline-first semantic & keyword vector index with TF-IDF/BM25 cosine scoring
    and optional ChromaDB integration.
    """
    def __init__(self, persist_dir: Optional[Path] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self._docs: Dict[str, DecisionSlice] = {}
        self._corpus_texts: Dict[str, str] = {}
        self._idf: Dict[str, float] = {}

    def _tokenize(self, text: str) -> List[str]:
        # Normalize and tokenize alphanumeric & CJK characters
        import re
        text = text.lower()
        tokens = re.findall(r"[\w\u4e00-\u9fa5]+", text)
        return tokens

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0.0) + 1.0
        total = max(1.0, float(len(tokens)))
        return {k: v / total for k, v in tf.items()}

    def _update_idf(self):
        doc_count = len(self._corpus_texts)
        if doc_count == 0:
            return
        doc_freq = {}
        for text in self._corpus_texts.values():
            unique_tokens = set(self._tokenize(text))
            for token in unique_tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1
        
        self._idf = {
            token: math.log((doc_count + 1.0) / (df + 1.0)) + 1.0
            for token, df in doc_freq.items()
        }

    def upsert_slice(self, decision: DecisionSlice):
        """Indexes a DecisionSlice into semantic vector store."""
        doc_text = (
            f"Pattern: {decision.pattern_name} {decision.pattern_name}\n"
            f"Category: {decision.category.value}\n"
            f"Standard: {decision.standard_reference.value}\n"
            f"Problem: {decision.problem_statement}\n"
            f"Solution: {decision.chosen_solution_summary}\n"
            f"Constraints: {json.dumps(decision.context_constraints.model_dump())}\n"
            f"Tradeoffs: {'; '.join([t.dimension + ': ' + t.advantage + ' vs ' + t.disadvantage for t in decision.tradeoffs])}\n"
            f"Failure Modes: {'; '.join([f.trigger_condition + ' -> ' + f.consequence for f in decision.failure_modes])}"
        )
        self._docs[decision.id] = decision
        self._corpus_texts[decision.id] = doc_text
        self._update_idf()

    def query_similar(self, query: str, top_k: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Computes cosine similarity of TF-IDF vectors for query against corpus."""
        query_tokens = self._tokenize(query)
        if not query_tokens or not self._docs:
            return [{"id": doc_id, "similarity": 0.5, "metadata": {"id": doc_id}} for doc_id in list(self._docs.keys())[:top_k]]

        query_tf = self._compute_tf(query_tokens)
        query_vec = {t: query_tf[t] * self._idf.get(t, 1.0) for t in query_tokens}
        query_norm = math.sqrt(sum(v * v for v in query_vec.values())) or 1.0

        scores = []
        for doc_id, doc_text in self._corpus_texts.items():
            doc = self._docs[doc_id]
            doc_tokens = self._tokenize(doc_text)
            doc_tf = self._compute_tf(doc_tokens)
            doc_vec = {t: doc_tf[t] * self._idf.get(t, 1.0) for t in doc_tokens}
            doc_norm = math.sqrt(sum(v * v for v in doc_vec.values())) or 1.0

            # Dot product
            dot = sum(query_vec.get(t, 0.0) * doc_vec.get(t, 0.0) for t in query_tokens)
            cosine_sim = dot / (query_norm * doc_norm)

            # Bonus for exact title keyword matching
            for token in query_tokens:
                if token in doc.pattern_name.lower():
                    cosine_sim += 0.25

            scores.append((doc_id, min(1.0, cosine_sim)))

        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for doc_id, sim in scores[:top_k]:
            results.append({
                "id": doc_id,
                "similarity": round(sim, 4),
                "metadata": {"id": doc_id, "pattern_name": self._docs[doc_id].pattern_name}
            })
        return results
