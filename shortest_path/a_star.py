import osmnx as ox
from networkx import MultiDiGraph
from typing import Dict, List
import random
import requests
import heapq

from .modules.utils import style_unvisited_edge, style_visited_edge, style_active_edge, style_path_edge, plot_graph, reconstruct_path, create_simple_graph, find_distance_by_nodes, clean_max_speed
from .modules.simple_graph import Node

def a_star(graph: MultiDiGraph, simple_graph: Dict[int, Node], source: int, destination: int, plot=False) -> bool:
  for edge in graph.edges:
    style_unvisited_edge(graph, edge)

  iteration = 0
  priority_queue = [(0, source)]
  simple_graph[source].visited = True
  while priority_queue:
    _, node = heapq.heappop(priority_queue)
    if node == destination:
      if plot:
        plot_graph(graph, simple_graph, algorithm=f"a_star-exploration_{iteration:08d}", dpi=1024)
      return True

    for edge in graph.out_edges(node):
      current_node: int = edge[0]
      next_node: int = edge[1]
      visited_edge = (current_node, next_node, 0)
      style_visited_edge(graph, visited_edge)

      if simple_graph[next_node].visited:
        continue

      iteration += 1
      edge_weight: float = graph.edges[visited_edge]["length"] / 1000
      total_weight: float = edge_weight + find_distance_by_nodes(graph, next_node, destination)
      total_weight /= graph.edges[visited_edge]["maxspeed"]
      if simple_graph[next_node].distance > simple_graph[node].distance + total_weight:
        simple_graph[next_node].visited = True
        simple_graph[next_node].distance = simple_graph[node].distance + total_weight
        simple_graph[next_node].previous = node
        heapq.heappush(priority_queue, (simple_graph[next_node].distance, next_node))
        for active_edges in graph.out_edges(next_node):
          style_active_edge(graph, (active_edges[0], active_edges[1], 0))
      # if iteration%10 == 0:
        # plot_graph(graph, simple_graph, algorithm=f"a_star-exploration_{iteration//10:08d}", dpi=384)
  return False

def run_a_star(location=None, source_point=None, destination_point=None) -> None:
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

  if a_star(G, simple_graph, source, destination, plot=True):
    reconstruct_path(G, simple_graph, source, destination, plot=True, algorithm="a_star")
  else:
    print("Failed to find a path")