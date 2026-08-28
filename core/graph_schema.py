from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    PATTERN = "Pattern"
    CATEGORY = "Category"
    INFRA_DEPENDENCY = "InfraDependency"
    FAILURE_MODE = "FailureMode"
    ALTERNATIVE = "Alternative"
    STANDARD = "Standard"

class EdgeType(str, Enum):
    BELONGS_TO_CATEGORY = "BELONGS_TO_CATEGORY"
    STANDARDIZED_BY = "STANDARDIZED_BY"
    REQUIRES_INFRA = "REQUIRES_INFRA"
    HAS_FAILURE_MODE = "HAS_FAILURE_MODE"
    COMPETES_WITH = "COMPETES_WITH"
    SUPERSEDES = "SUPERSEDES"
    MIGRATED_FROM = "MIGRATED_FROM"

class GraphNode(BaseModel):
    id: str
    type: NodeType
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    source: str
    target: str
    type: EdgeType
    properties: Dict[str, Any] = Field(default_factory=dict)
