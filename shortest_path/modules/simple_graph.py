from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

class Node:
  visited: bool
  distance: float
  previous: Optional[int]
  size: float
  alpha: float
  node_type: str

NodeId = int
EdgeId = Tuple[NodeId, NodeId]

@dataclass
class RawNode:
  id: NodeId
  next_nodes: List[NodeId]

@dataclass
class Edge:
  id: EdgeId
  length: float
  maxspeed: int

@dataclass
class Graph:
  nodes: Dict[NodeId, RawNode]
  edges: Dict[EdgeId, Edge]