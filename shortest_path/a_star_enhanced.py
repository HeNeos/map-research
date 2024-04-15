import osmnx as ox
from networkx import MultiDiGraph
from typing import Dict, List
import random
import requests
import heapq

from .modules.utils import style_unvisited_edge, style_visited_edge, style_active_edge, style_path_edge, plot_graph, create_simple_graph, find_distance_by_nodes
from .modules.simple_graph import Node


def clean_max_speed(graph: MultiDiGraph) -> None:
  for edge in graph.edges:
    edge_data = graph.edges[edge]
    max_speed = 30
    if "maxspeed" in edge_data:
      max_speeds = edge_data["maxspeed"]
      if isinstance(max_speeds, list):
        speeds: List[int] = [ int(speed) for speed in max_speeds if speed and speed.isnumeric() ]
        if len(speeds) > 0:
          max_speed = min(speeds)
      elif isinstance(max_speeds, str) and max_speeds.isnumeric():
        max_speed = int(max_speeds)
    edge_data["maxspeed"] = max_speed

def a_star_enhanced(graph: MultiDiGraph, simple_graph: Dict[int, Node], source: int, destination: int, plot=False) -> bool:
  for edge in graph.edges:
    style_unvisited_edge(graph, edge)

  iteration = 0
  priority_queue = [(0, source)]
  simple_graph[source].visited = True
  best_node_distance = None
  source_to_destination_min_distance = find_distance_by_nodes(graph, source, destination)
  while priority_queue:
    _, node = heapq.heappop(priority_queue)
    if node == destination:
      if plot:
        plot_graph(graph, simple_graph, algorithm=f"a_star_enhanced-exploration_{iteration:08d}", dpi=384)
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
      destination_distance = find_distance_by_nodes(graph, next_node, destination)
      source_distance = find_distance_by_nodes(graph, source, current_node)

      if simple_graph[current_node].distance == 0:
        scale_factor = 1
      else:
        scale_factor = source_distance / simple_graph[current_node].distance
      expected_distance = destination_distance / scale_factor

      total_weight: float = edge_weight + (0.5*destination_distance + 0.5*expected_distance)
      edge_max_speed = graph.edges[visited_edge]["maxspeed"]
      total_weight /= edge_max_speed
      if simple_graph[next_node].distance > simple_graph[node].distance + total_weight:
        simple_graph[next_node].visited = True
        simple_graph[next_node].distance = simple_graph[node].distance + total_weight
        simple_graph[next_node].previous = node
        if best_node_distance:
          if destination_distance > best_node_distance:
            continue
          else:
            best_node_distance = max(destination_distance, source_to_destination_min_distance)
        else:
          best_node_distance = destination_distance
        heapq.heappush(priority_queue, (simple_graph[next_node].distance, next_node))
        for active_edges in graph.out_edges(next_node):
          style_active_edge(graph, (active_edges[0], active_edges[1], 0))
      # if iteration%5 == 0:
      #   plot_graph(graph, simple_graph, algorithm=f"a_star_enhanced-exploration_{iteration//5:08d}", dpi=384)
  return False

def reconstruct_path(graph: MultiDiGraph, simple_graph: Dict[int, Node], source: int, destination: int, plot=False, algorithm=None) -> None:
  for edge in graph.edges:
    style_unvisited_edge(graph, edge)

  dist: float = 0
  time: float = 0
  current: int = destination
  while current != source:
    previous: int = simple_graph[current].previous
    edge_data = graph.edges[(previous, current, 0)]
    current_length = edge_data["length"] / 1000
    current_max_speed = edge_data["maxspeed"]
    dist += current_length
    time += current_length / current_max_speed
    style_path_edge(graph, (previous, current, 0))
    if algorithm:
      edge_data[f"{algorithm}_uses"] = edge_data.get(f"{algorithm}_uses", 0) + 1
    current = previous
  if plot:
    time_sec = time * 60 * 60
    print(f"Total dist = {dist} km")
    print(f"Total time = {int (time_sec // 60)} m {int(time_sec % 60)} sec")
    print(f"Speed average = {dist / time}")
    plot_graph(graph, simple_graph, algorithm="a_star_enhanced-path", dpi=1024)

def run_a_star_enhanced(location=None, source_point=None, destination_point=None) -> None:
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

  simple_graph: Dict[int, Node] = create_simple_graph(G)

  simple_graph[source].distance = 0
  simple_graph[source].size = 35
  simple_graph[source].alpha = 1
  simple_graph[source].node_type = "source"

  simple_graph[destination].size = 35
  simple_graph[destination].alpha = 1
  simple_graph[destination].node_type = "destination"

  if a_star_enhanced(G, simple_graph, source, destination, plot=True):
    reconstruct_path(G, simple_graph, source, destination, plot=True, algorithm="a_star_enhanced")
  else:
    print("Failed to find a path")