import json
import logging
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import networkx as nx
from core.schema import DecisionSlice
from core.graph_schema import NodeType, EdgeType
from config.settings import settings

logger = logging.getLogger(__name__)

class EvidenceGraph:
    """
    Knowledge & Evidence Graph capturing relationships among:
    Patterns, Categories, Standards, Required Infrastructure, Failure Modes, and Competing Alternatives.
    """
    def __init__(self, persist_file: Optional[Path] = None):
        self.persist_file = persist_file or settings.GRAPH_PERSIST_FILE
        self.graph = nx.DiGraph()
        self.load_graph()

    def add_decision_slice(self, decision: DecisionSlice):
        """Adds a DecisionSlice and all its relational entities into the graph."""
        pattern_node_id = f"pattern:{decision.id}"
        
        # 1. Main Pattern Node
        self.graph.add_node(
            pattern_node_id,
            node_type=NodeType.PATTERN.value,
            id=decision.id,
            pattern_name=decision.pattern_name,
            confidence_score=decision.confidence_score,
            evidence_level=decision.evidence.evidence_level.value,
            status=decision.status.value,
            category=decision.category.value,
            raw_data=decision.model_dump()
        )

        # 2. Category Node & Edge
        cat_node_id = f"category:{decision.category.value}"
        self.graph.add_node(cat_node_id, node_type=NodeType.CATEGORY.value, name=decision.category.value)
        self.graph.add_edge(pattern_node_id, cat_node_id, edge_type=EdgeType.BELONGS_TO_CATEGORY.value)

        # 3. Standard Reference Node & Edge
        std_node_id = f"standard:{decision.standard_reference.value}"
        self.graph.add_node(std_node_id, node_type=NodeType.STANDARD.value, name=decision.standard_reference.value)
        self.graph.add_edge(pattern_node_id, std_node_id, edge_type=EdgeType.STANDARDIZED_BY.value)

        # 4. Infrastructure Dependencies
        for infra in decision.context_constraints.infra_dependencies:
            infra_node_id = f"infra:{infra.lower()}"
            self.graph.add_node(infra_node_id, node_type=NodeType.INFRA_DEPENDENCY.value, name=infra)
            self.graph.add_edge(pattern_node_id, infra_node_id, edge_type=EdgeType.REQUIRES_INFRA.value)

        # 5. Failure Modes
        for i, fm in enumerate(decision.failure_modes):
            fm_node_id = f"failure:{decision.id}_{i}"
            self.graph.add_node(
                fm_node_id,
                node_type=NodeType.FAILURE_MODE.value,
                trigger=fm.trigger_condition,
                consequence=fm.consequence,
                mitigation=fm.mitigation_strategy
            )
            self.graph.add_edge(pattern_node_id, fm_node_id, edge_type=EdgeType.HAS_FAILURE_MODE.value)

        # 6. Competing Alternatives
        for alt in decision.considered_alternatives:
            alt_node_id = f"alt:{alt.name.lower()}"
            self.graph.add_node(alt_node_id, node_type=NodeType.ALTERNATIVE.value, name=alt.name)
            self.graph.add_edge(
                pattern_node_id,
                alt_node_id,
                edge_type=EdgeType.COMPETES_WITH.value,
                rejected_reason=alt.rejected_reason
            )

    def get_pattern_by_id(self, slice_id: str) -> Optional[Dict[str, Any]]:
        node_id = f"pattern:{slice_id}"
        if self.graph.has_node(node_id):
            return self.graph.nodes[node_id].get("raw_data")
        return None

    def filter_patterns_by_constraints(
        self,
        allowed_infra: Optional[List[str]] = None,
        disallowed_infra: Optional[List[str]] = None,
        min_confidence: float = 0.5,
        required_category: Optional[str] = None
    ) -> Set[str]:
        """
        Graph query: returns slice IDs that satisfy hard infrastructural and categorical constraints.
        """
        candidate_ids = set()
        for node_id, data in self.graph.nodes(data=True):
            if data.get("node_type") == NodeType.PATTERN.value:
                # Confidence filter
                if data.get("confidence_score", 1.0) < min_confidence:
                    continue
                # Status filter
                if data.get("status") == "Deprecated":
                    continue
                # Category filter
                if required_category and data.get("category") != required_category:
                    continue

                # Check required infra out-edges
                infra_dependencies = [
                    self.graph.nodes[target]["name"].lower()
                    for _, target, edge_data in self.graph.out_edges(node_id, data=True)
                    if edge_data.get("edge_type") == EdgeType.REQUIRES_INFRA.value
                ]

                # If user specified disallowed infra (e.g. no Redis, no Kafka)
                if disallowed_infra:
                    disallowed_set = {i.lower() for i in disallowed_infra}
                    if any(dep in disallowed_set for dep in infra_dependencies):
                        continue

                # If user specified strictly allowed infra
                if allowed_infra is not None:
                    allowed_set = {i.lower() for i in allowed_infra}
                    if any(dep not in allowed_set for dep in infra_dependencies):
                        continue

                candidate_ids.add(data.get("id"))
        return candidate_ids

    def save_graph(self):
        """Persists the graph to JSON."""
        data = nx.node_link_data(self.graph, edges="edges")
        with open(self.persist_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Evidence graph saved to {self.persist_file}")

    def load_graph(self):
        """Loads graph from JSON if exists."""
        if self.persist_file.exists():
            try:
                with open(self.persist_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.graph = nx.node_link_graph(data, edges="edges")
                logger.info(f"Loaded evidence graph with {len(self.graph.nodes)} nodes.")
            except Exception as e:
                logger.warning(f"Failed to load existing evidence graph: {e}")
                self.graph = nx.DiGraph()
