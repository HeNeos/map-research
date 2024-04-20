import osmnx as ox
from networkx import MultiDiGraph
from typing import Dict, List
import random
import requests
import heapq

from .modules.utils import style_unvisited_edge, style_visited_edge, style_active_edge, style_path_edge, plot_graph, reconstruct_path, create_simple_graph, clean_max_speed
from .modules.simple_graph import Node

def dijkstra(graph: MultiDiGraph, simple_graph: Dict[int, Node], source: int, destination: int, plot=False, dpi=2048) -> bool:
  for edge in graph.edges:
    style_unvisited_edge(graph, edge)

  iteration = 0
  priority_queue = [(0, source)]
  while priority_queue:
    _, node = heapq.heappop(priority_queue)
    if node == destination:
      if plot:
        plot_graph(graph, simple_graph, algorithm=f"dijkstra_assets/dijkstra-exploration_{iteration:08d}_{dpi}", dpi=dpi)
      return True

    if simple_graph[node].visited:
      continue
    simple_graph[node].visited = True

    for edge in graph.out_edges(node):
      iteration += 1
      current_node: int = edge[0]
      next_node: int = edge[1]
      visited_edge = (current_node, next_node, 0)
      style_visited_edge(graph, visited_edge)

      edge_weight: float = (graph.edges[visited_edge]["length"] / 1000) / graph.edges[visited_edge]["maxspeed"]
      if simple_graph[next_node].distance > simple_graph[node].distance + edge_weight:
        simple_graph[next_node].distance = simple_graph[node].distance + edge_weight
        simple_graph[next_node].previous = node
        heapq.heappush(priority_queue, (simple_graph[next_node].distance, next_node))
        for active_edges in graph.out_edges(next_node):
          style_active_edge(graph, (active_edges[0], active_edges[1], 0))
      # if iteration%90 == 0:
      #   plot_graph(graph, simple_graph, algorithm=f"dijkstra_assets/dijkstra-exploration_{iteration//90:08d}", dpi=450)
  return False

def run_dijkstra(location=None, source_point=None, destination_point=None) -> None:
  if location is None or source_point is None:
    response = requests.get("https://ipinfo.io")
    response_json = response.json()
    location = f"{response_json['city']}, {response_json['country']}"
    source_point = response_json["loc"].strip()

  source_point = source_point.split(",")

  latitude, longitude = source_point
  latitude = float(latitude)
  longitude = float(longitude)

  try:
    print("Loading graph...")
    G: MultiDiGraph = ox.graph_from_place(location, network_type="drive")
    print("Successfully loaded graph")
  except:
    print("Failed to load the graph")
    raise Exception

  clean_max_speed(G)

  source = ox.nearest_nodes(G, longitude, latitude)
  if destination_point is None:
    destination = random.choice(list(G.nodes))
  else:
    destination_latitude, destination_longitude = destination_point.split(",")
    destination = ox.nearest_nodes(G, float(destination_longitude), float(destination_latitude))

  simple_graph: Dict[int, Node] = create_simple_graph(G, source, destination)

  if dijkstra(G, simple_graph, source, destination, plot=True):
    reconstruct_path(G, simple_graph, source, destination, plot=True, algorithm="dijkstra")
  else:
    print("Failed to find a path")