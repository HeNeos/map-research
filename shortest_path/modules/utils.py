import osmnx as ox
from networkx import MultiDiGraph
from typing import Optional, Dict, List, Tuple
from .simple_graph import Node, RawNode, NodeId, Edge, EdgeId, Graph
import matplotlib.pyplot as plt
from haversine import haversine


class UnvisitedEdge:
    color = plt.cm.viridis(0.25)
    alpha = 0.4
    linewidth = 0.4


class VisitedEdge:
    color = plt.cm.viridis(0.45)
    alpha = 0.6
    linewidth = 0.5


class ActiveEdge:
    color = plt.cm.viridis(0.7)
    alpha = 0.8
    linewidth = 0.6


class PathEdge:
    color = plt.cm.viridis(1.0)
    alpha = 1.0
    linewidth = 0.7


NODE_SIZE = 0.20
NODE_ALPHA = 0.08

POINT_SIZE = 18
POINT_ALPHA = 1


def style_unvisited_edge(graph: MultiDiGraph, edge) -> None:
    graph.edges[edge]["color"] = UnvisitedEdge.color
    graph.edges[edge]["alpha"] = UnvisitedEdge.alpha
    graph.edges[edge]["linewidth"] = UnvisitedEdge.linewidth


def style_visited_edge(graph: MultiDiGraph, edge) -> None:
    graph.edges[edge]["color"] = VisitedEdge.color
    graph.edges[edge]["alpha"] = VisitedEdge.alpha
    graph.edges[edge]["linewidth"] = VisitedEdge.linewidth


def style_active_edge(graph: MultiDiGraph, edge) -> None:
    graph.edges[edge]["color"] = ActiveEdge.color
    graph.edges[edge]["alpha"] = ActiveEdge.alpha
    graph.edges[edge]["linewidth"] = ActiveEdge.linewidth


def style_path_edge(graph: MultiDiGraph, edge) -> None:
    graph.edges[edge]["color"] = PathEdge.color
    graph.edges[edge]["alpha"] = PathEdge.alpha
    graph.edges[edge]["linewidth"] = PathEdge.linewidth


def plot_graph_raw(graph: MultiDiGraph, edges_in_path: List[EdgeId]):
    destination = edges_in_path[0][-1]
    source = edges_in_path[-1][0]
    ox.plot_graph(
        graph,
        node_size=[
            POINT_SIZE if node in (source, destination) else NODE_SIZE
            for node in graph.nodes
        ],
        node_alpha=[
            POINT_ALPHA if node in (source, destination) else NODE_ALPHA
            for node in graph.nodes
        ],
        edge_color=[
            (
                PathEdge.color
                if (edge[0], edge[1]) in edges_in_path
                else UnvisitedEdge.color
            )
            for edge in graph.edges
        ],
        edge_alpha=[
            (
                PathEdge.alpha
                if (edge[0], edge[1]) in edges_in_path
                else UnvisitedEdge.alpha
            )
            for edge in graph.edges
        ],
        edge_linewidth=[
            (
                PathEdge.linewidth
                if (edge[0], edge[1]) in edges_in_path
                else UnvisitedEdge.linewidth
            )
            for edge in graph.edges
        ],
        node_color=[
            (
                "white"
                if node not in (source, destination)
                else "blue" if node == source else "red"
            )
            for node in graph.nodes
        ],
        bgcolor="#000000",
        show=True,
        save=False,
        dpi=256,
    )
    plt.close()


def plot_graph(
    graph: MultiDiGraph,
    simple_graph: Dict[int, Node],
    iteration: int,
    algorithm: str = "default",
    time: Optional[float] = None,
    dist: Optional[float] = None,
    dpi: int = 1024,
) -> None:
    node_colors = {"source": "blue", "destination": "red", "default": "white"}
    fig, ax = ox.plot_graph(
        graph,
        node_size=[simple_graph[node].size for node in graph.nodes],
        node_alpha=[simple_graph[node].alpha for node in graph.nodes],
        edge_color=[graph.edges[edge]["color"] for edge in graph.edges],
        edge_alpha=[graph.edges[edge]["alpha"] for edge in graph.edges],
        edge_linewidth=[graph.edges[edge]["linewidth"] for edge in graph.edges],
        node_color=[
            node_colors.get(simple_graph[node].node_type, "white")
            for node in graph.nodes
        ],
        bgcolor="#000000",
        show=False,
        save=False,
        close=False,
    )
    titles = "\n".join(
        [
            f"{title_name}: {title_value}"
            for (title_name, title_value) in [
                ("Iteration", iteration),
                ("Time", time),
                ("Distance", dist),
            ]
            if title_value is not None
        ]
    )
    ax.set_title(titles, color="#3b528b", fontsize=10)

    plt.savefig(f"./assets/{algorithm}.png", dpi=dpi, format="png")
    plt.close()


def plot_heatmap(graph: MultiDiGraph, algorithm) -> None:
    edge_colors = ox.plot.get_edge_colors_by_attr(
        graph, f"{algorithm}_uses", cmap="hot"
    )
    fig, _ = ox.plot_graph(
        graph, node_size=0, edge_color=edge_colors, bgcolor="#000000"
    )


def reconstruct_path(
    graph: MultiDiGraph,
    simple_graph: Dict[int, Node],
    source: int,
    destination: int,
) -> Tuple[float, float]:
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
        # if algorithm:
        #     edge_data[f"{algorithm}_uses"] = edge_data.get(f"{algorithm}_uses", 0) + 1
        current = previous
    time_sec = time * 60 * 60
    print(f"Total dist = {dist} km")
    print(f"Total time = {int (time_sec // 60)} m {int(time_sec % 60)} sec")
    print(f"Speed average = {dist / time}")
    return dist, time_sec


def find_nearest_node_from_point(graph: MultiDiGraph, latitude, longitude) -> int:
    nearest_node: Optional[int] = None
    min_distance: Optional[float] = None
    for node in graph.nodes:
        current_latitude: float = float(graph.nodes[node]["y"])
        current_longitude: float = float(graph.nodes[node]["x"])
        distance = haversine(
            (longitude, latitude), (current_longitude, current_latitude)
        )
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

    return haversine(
        (source_longitude, source_latitude),
        (destination_longtiude, destination_latitude),
    )


def create_simple_graph(
    graph: MultiDiGraph, source: int, destination: int
) -> Dict[int, Node]:
    simple_graph: Dict[int, Node] = dict()
    for node in graph.nodes:
        simple_graph[node] = Node()
        simple_graph[node].visited = False
        simple_graph[node].distance = float("inf")
        simple_graph[node].previous = None
        simple_graph[node].size = NODE_SIZE
        simple_graph[node].alpha = NODE_ALPHA
        simple_graph[node].node_type = "default"

    simple_graph[source].distance = 0
    simple_graph[source].size = POINT_SIZE
    simple_graph[source].alpha = POINT_ALPHA
    simple_graph[source].node_type = "source"

    simple_graph[destination].size = POINT_SIZE
    simple_graph[destination].alpha = POINT_ALPHA
    simple_graph[destination].node_type = "destination"

    return simple_graph


def get_max_speed(edge, min_max_speed_allowed=30):
    max_speed = min_max_speed_allowed
    if "maxspeed" in edge:
        max_speeds = edge["maxspeed"]
        if isinstance(max_speeds, list):
            speeds: List[int] = [
                int(speed) for speed in max_speeds if speed and speed.isnumeric()
            ]
            if len(speeds) > 0:
                max_speed = min(speeds)
        elif isinstance(max_speeds, str) and max_speeds.isnumeric():
            max_speed = int(max_speeds)
        elif isinstance(max_speeds, int):
            max_speed = max_speeds
    return max_speed


def clean_max_speed(graph: MultiDiGraph, return_max_speed=False) -> Optional[float]:
    min_max_speed_allowed = 30
    max_speed_allowed = 30
    for edge in graph.edges:
        edge_data = graph.edges[edge]
        max_speed = get_max_speed(edge_data, min_max_speed_allowed)
        edge_data["maxspeed"] = max_speed
        max_speed_allowed = max(max_speed, max_speed_allowed)
    if return_max_speed:
        return max_speed_allowed


def convert_multidigraph_to_graph(graph: MultiDiGraph) -> Graph:
    all_edges: Dict[EdgeId, Edge] = dict()
    to_node_by_node: Dict[NodeId, List[NodeId]] = dict()
    for edge in graph.edges:
        u, v, _ = edge
        current_edge = graph.edges[edge]
        all_edges[(u, v)] = Edge(
            id=(u, v),
            length=current_edge["length"],
            maxspeed=get_max_speed(current_edge),
        )
        if u not in to_node_by_node:
            to_node_by_node[u] = []
        to_node_by_node[u].append(v)

    all_nodes: Dict[NodeId, RawNode] = {
        node: RawNode(id=node, next_nodes=to_node_by_node.get(node, []))
        for node in graph.nodes
    }
    return Graph(nodes=all_nodes, edges=all_edges)


def load_multidigraph(location: str) -> MultiDiGraph:
    try:
        print("Loading graph...")
        G: MultiDiGraph = ox.graph_from_place(location, network_type="drive")
        print("Successfully loaded graph")
    except ValueError:
        print("Failed to load the graph")
        raise Exception
    return G
