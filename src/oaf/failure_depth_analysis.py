import networkx as nx


def analyze_failure_propagation_depth(failure_stats, graph):
    """
    Analyze the depth of failure propagation for each base node.

    :param failure_stats: Statistics on base failures for each node.
    :type failure_stats: dict of dict
    :param graph: Graph representing the node relationships.
    :type graph: nx.DiGraph

    :returns: A dictionary where keys are nodes and values are their failure propagation depths.
    :rtype: dict
    """
    # Shortest path lengths from each base node to all other nodes
    shortest_path_lengths = {node: nx.shortest_path_length(graph, node) for node in graph.nodes}

    mean_propagation_depths = {node: {'depth': -1., 'failures': 0} for node in graph.nodes}

    # Initialize propagation depth tracker
    propagation_depths = {node: [] for node in graph.nodes}

    # Iterate over all base failure nodes
    for downstream_node, base_causes in failure_stats.items():
        for base_cause, count in base_causes.items():
            # Calculate the propagation depth for each base cause
            propagation_depths[base_cause].append(shortest_path_lengths[downstream_node][base_cause])

    # Calculate the mean propagation depth for each node
    for node, depths in propagation_depths.items():
        if len(depths) == 0:
            continue
        mean_propagation_depths[node]['depth'] = sum(depths) / len(depths)
        mean_propagation_depths[node]['failures'] = len(depths)

    return mean_propagation_depths
