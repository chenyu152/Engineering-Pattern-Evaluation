import logging
from typing import List, Dict, Any
from core.schema import TaskAnalysisResult, DecisionSlice
from storage.hybrid_repository import HybridRepository

logger = logging.getLogger(__name__)

class PatternRetriever:
    """
    Coordinates dual-channel hybrid retrieval combining vector similarity and graph constraints.
    """
    def __init__(self, repository: HybridRepository):
        self.repository = repository

    def retrieve(self, task_analysis: TaskAnalysisResult, top_k: int = 3) -> List[Dict[str, Any]]:
        results = self.repository.hybrid_search(
            task_analysis=task_analysis,
            top_k=top_k,
            min_confidence=0.4
        )
        logger.info(f"Retrieved {len(results)} candidate patterns for task: '{task_analysis.raw_query[:40]}...'")
        return results
