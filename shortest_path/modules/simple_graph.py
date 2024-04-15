from typing import Optional, Dict

class Node:
  visited: bool
  distance: float
  previous: Optional[int]
  size: float
  alpha: float
  node_type: str