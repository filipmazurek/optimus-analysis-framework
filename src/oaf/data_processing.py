import networkx as nx
from collections import defaultdict
from itertools import combinations

from oaf.util import validate_check_data, validate_wave_data
from oaf.base_failure import find_base_failure_for_wave


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

        base_failure_nodes = set(base_failures.values())

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
        for node in base_failures.values():
            base_failure_counts[node] += 1

    return base_failure_counts


def split_data_by_wave(wave_data: list[dict]):
    """
    Sort and split simulation data into sublists where each list begins with a timed_trigger=True entry.
    If the first entry is not timed_trigger=True, it will be ignored.

    :param wave_data: The raw simulation data.
    :return: Sorted and split simulation data.
    """
    validate_wave_data(wave_data)

    #  Sort the by the 'wave' value
    sorted_data = sorted(wave_data, key=lambda x: x['wave'])

    # Split into sublists based on 'timed_trigger=True'
    split_data = []
    current_list = []

    for entry in sorted_data:
        if entry['timed_trigger']:
            # If a new propagation starts, save the current list and start a new one
            if current_list:
                split_data.append(current_list)
            current_list = [entry]  # Start a new list with this entry
        else:
            current_list.append(entry)

    # Append the last propagation step if not empty
    if current_list:
        split_data.append(current_list)

    return split_data


def organize_check_data_by_wave(wave_data, check_data):
    """
    Organize the check_data results by wave.

    :param wave_data: list of dict: The raw simulation data.
    :param check_data: list of dict: The check_data results.
    :return: dict: A dictionary where keys are wave numbers and values are the check_data results for that wave.
    """
    validate_wave_data(wave_data)
    validate_check_data(check_data)

    # Remove all data that is not a timed trigger
    wave_data = [entry for entry in wave_data if entry['timed_trigger']]

    # Sort by the 'wave' value
    sorted_sim_data = sorted(wave_data, key=lambda x: x['wave'])

    # Place all check_data results into the appropriate wave bucket
    organized_results = {}
    for i in range(len(sorted_sim_data)):
        low = sorted_sim_data[i]['wave']
        high = sorted_sim_data[i + 1]['wave'] if i + 1 < len(sorted_sim_data) else float('inf')
        organized_results[low] = [result for result in check_data if low <= result['wave'] < high]

    return organized_results


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
