import osmnx as ox
from networkx import MultiDiGraph
from typing import Dict, Optional
import random
import requests
import heapq

from .modules.utils import (
    style_unvisited_edge,
    style_visited_edge,
    style_active_edge,
    plot_graph,
    reconstruct_path,
    create_simple_graph,
    clean_max_speed,
    load_multidigraph,
)
from .modules.simple_graph import Node


def dijkstra(
    graph: MultiDiGraph,
    simple_graph: Dict[int, Node],
    source: int,
    destination: int,
    video: bool,
    algorithm_name="dijkstra",
) -> Optional[int]:
    for edge in graph.edges:
        style_unvisited_edge(graph, edge)

    iteration = 0
    priority_queue = [(0, source)]
    while priority_queue:
        _, node = heapq.heappop(priority_queue)
        if node == destination:
            return iteration

        if simple_graph[node].visited:
            continue
        simple_graph[node].visited = True

        for edge in graph.out_edges(node):
            iteration += 1
            current_node: int = edge[0]
            next_node: int = edge[1]
            visited_edge = (current_node, next_node, 0)
            style_visited_edge(graph, visited_edge)

            edge_weight: float = (
                graph.edges[visited_edge]["length"] / 1000
            ) / graph.edges[visited_edge]["maxspeed"]
            if (
                simple_graph[next_node].distance
                > simple_graph[node].distance + edge_weight
            ):
                simple_graph[next_node].distance = (
                    simple_graph[node].distance + edge_weight
                )
                simple_graph[next_node].previous = node
                heapq.heappush(
                    priority_queue, (simple_graph[next_node].distance, next_node)
                )
                for active_edges in graph.out_edges(next_node):
                    style_active_edge(graph, (active_edges[0], active_edges[1], 0))
            if video:
                if iteration % 50 == 0:
                    frame_number = f"{iteration // 50:08d}"
                    plot_graph(
                        graph=graph,
                        simple_graph=simple_graph,
                        iteration=iteration,
                        algorithm=f"{algorithm_name}_assets/{algorithm_name}-exploration_{frame_number}",
                        dpi=256,
                    )
    return None


def run_dijkstra(
    location=None, source_point=None, destination_point=None, video=False
) -> None:
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

    clean_max_speed(G)

    source = ox.nearest_nodes(G, longitude, latitude)
    if destination_point is None:
        destination = random.choice(list(G.nodes))
    else:
        destination_latitude, destination_longitude = destination_point.split(",")
        destination = ox.nearest_nodes(
            G, float(destination_longitude), float(destination_latitude)
        )

    simple_graph: Dict[int, Node] = create_simple_graph(G, source, destination)

    algorithm_name = "dijkstra"
    iterations = dijkstra(
        graph=G,
        simple_graph=simple_graph,
        source=source,
        destination=destination,
        video=video,
        algorithm_name=algorithm_name,
    )
    if iterations is not None:
        dist, time = reconstruct_path(
            graph=G, simple_graph=simple_graph, source=source, destination=destination
        )
        plot_graph(
            graph=G,
            simple_graph=simple_graph,
            iteration=iterations,
            algorithm=f"{algorithm_name}_assets/{algorithm_name}-path",
            time=time,
            dist=dist,
            dpi=512,
        )
    else:
        print("Failed to find a path")
