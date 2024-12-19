from collections import defaultdict
from sys import base_exec_prefix

import networkx as nx

from oaf.data_processing import split_data_by_wave
from oaf.util import validate_wave_data


def _find_base_failure(wave_data, graph):
    """
    For a single trigger wave and possible diagnose waves, find the base cause of downstream failure.

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
        base_failures = _find_base_failure(wave, graph)

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
