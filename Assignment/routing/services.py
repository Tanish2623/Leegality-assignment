
from .models import Edge


def find_shortest_path(source_name, destination_name):
    if source_name == destination_name:
        return [source_name], 0.0

    connections = {}

    for edge in Edge.objects.select_related("source", "destination"):
        source = edge.source.name
        destination = edge.destination.name

        if source not in connections:
            connections[source] = []

        connections[source].append((destination, edge.latency))

    distances = {source_name: 0}
    previous_nodes = {}
    unvisited = {source_name}

    while unvisited:
        current_node = None
        shortest_distance = None

        for node in unvisited:
            distance = distances.get(node)

            if distance is not None:
                if shortest_distance is None or distance < shortest_distance:
                    shortest_distance = distance
                    current_node = node

        if current_node is None:
            break

        unvisited.remove(current_node)

        if current_node == destination_name:
            break

        for neighbour, latency in connections.get(current_node, []):
            new_distance = distances[current_node] + latency

            if (
                neighbour not in distances
                or new_distance < distances[neighbour]
            ):
                distances[neighbour] = new_distance
                previous_nodes[neighbour] = current_node
                unvisited.add(neighbour)

    if destination_name not in distances:
        return None, None

    route = []
    current_node = destination_name

    while current_node != source_name:
        route.append(current_node)
        current_node = previous_nodes[current_node]

    route.append(source_name)
    route.reverse()

    return route, distances[destination_name]
