import osmnx as ox
from networkx import MultiDiGraph
from typing import Optional, Dict
from .simple_graph import Node
import matplotlib.pyplot as plt

from math import radians, cos, sin, asin, sqrt

def style_unvisited_edge(graph: MultiDiGraph, edge) -> None:
  graph.edges[edge]["color"] = plt.cm.viridis(0.1)
  graph.edges[edge]["alpha"] = 0.35
  graph.edges[edge]["linewidth"] = 0.28

def style_visited_edge(graph: MultiDiGraph, edge) -> None:
  graph.edges[edge]["color"] = plt.cm.viridis(0.4)
  graph.edges[edge]["alpha"] = 0.45
  graph.edges[edge]["linewidth"] = 0.45

def style_active_edge(graph: MultiDiGraph, edge) -> None:
  graph.edges[edge]["color"] = plt.cm.viridis(0.7)
  graph.edges[edge]["alpha"] = 1.0
  graph.edges[edge]["linewidth"] = 0.65

def style_path_edge(graph: MultiDiGraph, edge) -> None:
  graph.edges[edge]["color"] = plt.cm.viridis(1.0)
  graph.edges[edge]["alpha"] = 1.0
  graph.edges[edge]["linewidth"] = 0.8

def plot_graph(graph: MultiDiGraph, simple_graph: Dict[int, Node], algorithm: str="default", dpi: int=1024) -> None:
  node_colors = {
    "source": "blue",
    "destination": "red",
    "default": "white"
  }
  ox.plot_graph(
    graph,
    node_size=[simple_graph[node].size for node in graph.nodes],
    node_alpha=[simple_graph[node].alpha for node in graph.nodes],
    edge_color=[graph.edges[edge]["color"] for edge in graph.edges],
    edge_alpha=[graph.edges[edge]["alpha"] for edge in graph.edges],
    edge_linewidth=[graph.edges[edge]["linewidth"] for edge in graph.edges],
    node_color=[node_colors.get(simple_graph[node].node_type, "white") for node in graph.nodes],
    bgcolor="#18080e",
    show=False,
    save=True,
    dpi=dpi,
    filepath=f"./assets/{algorithm}.png"
  )
  plt.close()

def plot_heatmap(graph: MultiDiGraph, algorithm) -> None:
  edge_colors = ox.plot.get_edge_colors_by_attr(graph, f"{algorithm}_uses", cmap="hot")
  fig, _ = ox.plot_graph(
    graph,
    node_size = 0,
    edge_color = edge_colors,
    bgcolor = "#18080e"
  )

def haversine(lon_1, lat_1, lon_2, lat_2):
  lon_1, lat_1, lon_2, lat_2 = map(radians, [lon_1, lat_1, lon_2, lat_2])

  dlon = lon_2 - lon_1 
  dlat = lat_2 - lat_1 
  a = sin(dlat/2)**2 + cos(lat_1) * cos(lat_2) * sin(dlon/2)**2
  c = 2 * asin(sqrt(a)) 
  r = 6371
  return c * r

def find_nearest_node_from_point(graph: MultiDiGraph, latitude, longitude) -> int:
  nearest_node: Optional[int] = None
  min_distance: Optional[float] = None
  for node in graph.nodes:
    current_latitude: float = float(graph.nodes[node]["y"])
    current_longitude: float = float(graph.nodes[node]["x"])
    distance = haversine(longitude, latitude, current_longitude, current_latitude)
    if min_distance is None or distance < min_distance:
      min_distance = distance
      nearest_node = node

  if nearest_node is None:
    raise Exception

  return nearest_node

def find_distance_by_nodes(graph: MultiDiGraph, source, destination):
  source_latitude = graph.nodes[source]["y"]
  source_longitude = graph.nodes[source]["x"]
  destination_latitude = graph.nodes[destination]["y"]
  destination_longtiude = graph.nodes[destination]["x"]

  return haversine(source_longitude, source_latitude, destination_longtiude, destination_latitude)

def create_simple_graph(graph: MultiDiGraph) -> Dict[int, Node]:
  simple_graph: Dict[int, Node] = dict()
  for node in graph.nodes:
    simple_graph[node] = Node()
    simple_graph[node].visited = False
    simple_graph[node].distance = float("inf")
    simple_graph[node].previous = None
    simple_graph[node].size = 1.02
    simple_graph[node].alpha = 0.08
    simple_graph[node].node_type = "default"
  
  return simple_graph