import networkx as nx
from collections import defaultdict
from itertools import combinations

from oaf.util import validate_check_data, validate_wave_data, split_data_by_wave


def time_to_failure(wave_data: list[dict], nodes: list[str]):
    """
    Find the time to failure for each node in the wave data.

    :param wave_data: Per-wave data
    :return: The time to failure for each node.
    """
    validate_wave_data(wave_data)
    time_to_failure = {node: [] for node in nodes}

    # Sort wave data by wave number
    wave_data.sort(key=lambda x: x['wave'])

    # Discard the first items in wave_data until the first timed_trigger=True entry
    while wave_data and not wave_data[0]['timed_trigger']:
        wave_data.pop(0)

    # Set up time_of_last_failure for each node. Default value is the beginning of the time period where everything is
    #   assumed to be newly calibrated.
    time_of_last_failure = {node: wave_data[0]['wave'] for node in nodes}

    # Iterate through the wave data, checking when each node failed
    for entry in wave_data:
        if entry['timed_trigger']:
            continue
        for node in entry['root_nodes']:
            time_to_failure[node].append(entry['wave'] - time_of_last_failure[node])
            time_of_last_failure[node] = entry['wave']

    return time_to_failure


def time_to_failure_base(wave_data: list[dict], graph: nx.DiGraph):
    """
    Find the time to base failure for each node in the wave data.

    :param wave_data: Per-wave data
    :param graph: The graph representing node relationships.
    :return: The time to base failure for each node.
    """
    validate_wave_data(wave_data)
    time_to_base_failure = {node: [] for node in graph.nodes}

    # Sort wave data by wave number
    # TODO: consodlidate all `sort` and `sorted` calls. This is messy.
    wave_data.sort(key=lambda x: x['wave'])

    # Set up time_of_last_failure for each node. Default value is the beginning of the time period where everything is
    #   assumed to be newly calibrated.
    time_of_last_failure = {node: wave_data[0]['wave'] for node in graph.nodes}

    split_wave_data = split_data_by_wave(wave_data)

    # Iterate through each wave, finding the time to base failure for each node
    for wave in split_wave_data:
        # Assume this to be the wave time for failure of these nodes
        failure_time = wave[0]['wave']

        # Get base failure causes for each case
        base_failures = find_base_failure_for_wave(wave, graph)
        flat_base_failures = [item for sublist in base_failures.values() for item in sublist]

        base_failure_nodes = set(flat_base_failures)

        for node in base_failure_nodes:
            time_to_base_failure[node].append(failure_time - time_of_last_failure[node])
            time_of_last_failure[node] = failure_time

    return time_to_base_failure


def count_failures(wave_data: list[dict], nodes: list[str]):
    """
    Count the number of failures per node using the wave data.
    This is intended for any time period in the wave data, to be used for SPA to find a CI for the number of failures in
    a given time period.

    :param wave_data: Raw per-wave simulation data.
    :return: The number of failures per node.
    """
    validate_wave_data(wave_data)
    node_failure_counts = {node: 0 for entry in wave_data for node in nodes}

    for entry in wave_data:
        if entry['timed_trigger']:
            continue
        for node in entry['root_nodes']:
            node_failure_counts[node] += 1

    return node_failure_counts


def count_base_failures(wave_data: list[dict], graph:nx.DiGraph):
    """
    Count the number of base failures per node using the wave data.
    This is intended for any time period in the wave data, to be used for SPA to find a CI for the number of base
    failures in a given time period.

    :param wave_data: Raw per-wave simulation data.
    :param graph: The graph representing node relationships.
    :return: The number of base failures per node.
    """
    validate_wave_data(wave_data)
    base_failure_counts = {node: 0 for entry in wave_data for node in graph.nodes}

    split_wave_data = split_data_by_wave(wave_data)

    for wave in split_wave_data:
        # Get base failure causes for each case
        base_failures = find_base_failure_for_wave(wave, graph)
        flat_base_failures = [item for sublist in base_failures.values() for item in sublist]
        base_failure_nodes = set(flat_base_failures)
        for node in base_failure_nodes:
            base_failure_counts[node] += 1

    return base_failure_counts


def find_co_occurring_failures(wave_data, nodes):
    """
    Find the co-occuring failures for each wave in Optimus

    :param wave_data: list of dict: List of wave data information.
    :return: dict of node tuples and their co-occurrence count.
    """
    validate_wave_data(wave_data)

    split_wave_data = split_data_by_wave(wave_data)

    cooccurrence_matrix = {}
    # Add all node combinations to the matrix
    for node1, node2 in combinations(nodes, 2):
        # Keep the pair sorted to ensure consistent key ordering
        pair = tuple(sorted((node1, node2)))
        cooccurrence_matrix[pair] = 0

    # Look through every set of diagnosis waves
    for wave in split_wave_data:
        failing_nodes = []
        # All nodes that fail check_data will start a diagnosis wave with the node as the root
        for entry in wave:
            if entry['timed_trigger']:
                continue
            failing_nodes += entry['root_nodes']

        for node1, node2 in combinations(failing_nodes, 2):
            pair = tuple(sorted((node1, node2)))
            cooccurrence_matrix[pair] += 1

    return cooccurrence_matrix


def find_base_failure_for_wave(wave_data, graph):
    """
    For a single trigger wave and possible diagnose waves, find the base cause of downstream failure.
    Note that this is only for a single wave and its diagnosis wave, not for all wave data.

    :param wave_data: list of dict: Wave data.
    :param graph: nx.DiGraph: The graph representing node relationships.
    :return: dict: A dictionary where keys are downstream nodes and values are lists of base causes.
    """
    validate_wave_data(wave_data)

    # Find all failed nodes
    failed_nodes = set()
    for wave in wave_data:
        if not wave['timed_trigger']:
            failed_nodes.update(wave['root_nodes'])

    # Identify the most downstream nodes
    # If the submitted node is in a timed_trigger wave, that is a base node
    downstream_nodes = set()
    for wave in wave_data:
        if wave['timed_trigger']:
            for node in wave['submitted_nodes']:
                if node in failed_nodes:
                    downstream_nodes.add(node)

    # Check that downstream nodes are not actually intermediate failures
    downstream_iterator = list(downstream_nodes)
    for node in downstream_iterator:
        predecessors = graph.predecessors(node)
        if any(predecessor in failed_nodes for predecessor in predecessors):
            downstream_nodes.remove(node)

    # Find base causes for each downstream node
    base_cause_map = {}  # Maps downstream nodes to their base causes
    for node in downstream_nodes:
        base_cause_map[node] = _find_base_cause(node, failed_nodes, graph)

    return base_cause_map


def _find_base_cause(node, failed_nodes, graph):
    """Identify the base cause of a failure by following the path of failures along the node graph."""
    base_causes = set()
    found_base_cause = False

    for successor in graph.successors(node):
        if successor in failed_nodes:
            found_base_cause = True
            base_causes.update(_find_base_cause(successor, failed_nodes, graph))

    if found_base_cause:
        return list(base_causes)
    else:
        return [node]


def find_base_failures(wave_data, graph):
    """
    Analyze failures and attribute base causes using failure paths.

    :param wave_data: list of dict: Wave data.
    :param graph: nx.DiGraph: The graph representing node relationships.
    :return: dict: A dictionary where keys are downstream nodes and values are lists of base causes.
    """
    validate_wave_data(wave_data)
    split_wave_data = split_data_by_wave(wave_data)

    base_failure_stats = defaultdict(lambda: defaultdict(int))

    for wave in split_wave_data:
        # Get base failure causes for each case
        base_failures = find_base_failure_for_wave(wave, graph)

        # Update the failure statistics
        for node, base_causes in base_failures.items():
            for cause in base_causes:
                base_failure_stats[node][cause] += 1

    return base_failure_stats


def _validate_base_failure_stats(base_failure_stats):
    """Validate the base failure statistics."""
    assert all(isinstance(node, str) for node in base_failure_stats.keys()), "Invalid node format."
    assert all(isinstance(causes, dict) for causes in base_failure_stats.values()), "Invalid cause format."
    assert all(isinstance(cause, str) for causes in base_failure_stats.values() for cause in causes.keys()), "Invalid cause format."
    assert all(isinstance(count, int) for causes in base_failure_stats.values() for count in causes.values()), "Invalid count format."


def calc_base_failure_proportion(failure_stats):
    """
    Calculate the proportion of base failures for each node.

    :param failure_stats: dict: A dictionary where keys are downstream nodes and values are dicts where the
    key is the base failure node and the value is the number of base failures caused by that node.
    """
    _validate_base_failure_stats(failure_stats)

    # Calculate proportions
    failure_proportions = defaultdict(lambda: defaultdict(float))
    for node, causes in failure_stats.items():
        total = sum(causes.values())
        for cause, count in causes.items():
            failure_proportions[node][cause] = count / total

    return failure_proportions


def find_mean_failure_chain_length(base_failure_stats, graph):
    """
    Calculate the average length of failure chains for each base node.

    :param failure_stats: dict: A dictionary where keys are downstream nodes and values are dicts where the
    key is the base failure node and the value is the number of base failures caused by that node.    """
    _validate_base_failure_stats(base_failure_stats)

    # If there exists a path between two nodes, calculate the length of the path
    path_lengths = {}
    for node in graph.nodes():
        path_lengths[node] = nx.single_source_shortest_path_length(graph, node)

    # Sum the lengths of the failure chains for each base node
    chain_lengths = {}
    for downstream_node, base_nodes in base_failure_stats.items():
        for base_node, num_failures in base_nodes.items():
            chain_lengths[base_node] = chain_lengths.get(base_node, []) + [
                path_lengths[downstream_node][base_node]] * num_failures

    # Calculate the average chain length for each base node
    average_chain_lengths = {}
    for base_node, lengths in chain_lengths.items():
        average_chain_lengths[base_node] = sum(lengths) / len(lengths)

    nodes = graph.nodes()
    average_chain_lengths_per_node = {x: average_chain_lengths.get(x, 0) for x in nodes}

    return average_chain_lengths_per_node


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
