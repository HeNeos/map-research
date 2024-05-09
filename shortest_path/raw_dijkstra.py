import osmnx as ox
from networkx import MultiDiGraph
from typing import Dict, List, Optional, Set
import random
import requests
import heapq

from .modules.utils import (
    plot_graph_raw,
    convert_multidigraph_to_graph,
    load_multidigraph,
)
from .modules.simple_graph import RawNode, NodeId, Edge, EdgeId, Graph


def dijkstra_raw(graph: Graph, source: int, destination: int) -> Optional[int]:
    weight_from_source: Dict[NodeId, float] = dict()
    visited_nodes: Set[NodeId] = set()
    previous_node: Dict[NodeId, Optional[NodeId]] = dict()

    iteration = 0
    priority_queue = [(0, source)]
    previous_node[source] = None
    while priority_queue:
        current_weight, current_node_id = heapq.heappop(priority_queue)
        if current_node_id == destination:
            return iteration, weight_from_source, previous_node
        current_node: RawNode = graph.nodes[current_node_id]
        if current_node_id in visited_nodes:
            continue
        visited_nodes.add(current_node_id)
        next_nodes_id: List[NodeId] = current_node.next_nodes
        for next_node_id in next_nodes_id:
            iteration += 1

            current_edge_id: EdgeId = (current_node_id, next_node_id)
            current_edge: Edge = graph.edges[current_edge_id]
            edge_weight = (current_edge.length / 1000) / current_edge.maxspeed

            new_weight = current_weight + edge_weight
            if weight_from_source.get(next_node_id, float("inf")) > new_weight:
                weight_from_source[next_node_id] = new_weight
                previous_node[next_node_id] = current_node_id
                heapq.heappush(priority_queue, (new_weight, next_node_id))
    return None


def reconstruct_path_raw(
    G: MultiDiGraph,
    graph: Graph,
    source: NodeId,
    destination: NodeId,
    path: Dict[NodeId, Optional[NodeId]],
):
    dist: float = 0
    time: float = 0
    edges_in_path: List[EdgeId] = []
    current_node_id: NodeId = destination
    while current_node_id != source:
        previous_node_id: NodeId = path[current_node_id]
        current_edge_id: EdgeId = (previous_node_id, current_node_id)
        edges_in_path.append(current_edge_id)
        current_edge: Edge = graph.edges[current_edge_id]
        current_length = current_edge.length
        current_maxspeed = current_edge.maxspeed
        dist += current_length / 1000
        time += (current_length / 1000) / current_maxspeed
        current_node_id = previous_node_id
    time_in_sec = int(time * 60 * 60)
    print(f"Total dist = {dist} km")
    print(f"Total time = {time_in_sec // 60} min {time_in_sec%60} sec")
    print(f"Speed average = {dist / time}")
    plot_graph_raw(G, edges_in_path)


def run_raw_dijkstra(location=None, source_point=None, destination_point=None) -> None:
    if location is None or source_point is None:
        response = requests.get("https://ipinfo.io")
        response_json = response.json()
        location = f"{response_json['city']}, {response_json['country']}"
        source_point = response_json["loc"].strip()

    source_point = source_point.split(",")

    latitude, longitude = source_point
    latitude = float(latitude)
    longitude = float(longitude)

    G: MultiDiGraph = load_multidigraph(location)

    source = ox.nearest_nodes(G, longitude, latitude)
    if destination_point is None:
        destination = random.choice(list(G.nodes))
    else:
        destination_latitude, destination_longitude = destination_point.split(",")
        destination = ox.nearest_nodes(
            G, float(destination_longitude), float(destination_latitude)
        )

    graph = convert_multidigraph_to_graph(G)

    result = dijkstra_raw(graph, source, destination)
    if result is not None:
        iterations, distances, path = result
        print(f"Iterations: {iterations}")
        reconstruct_path_raw(G, graph, source, destination, path)
    else:
        print("Failed to find a path")
