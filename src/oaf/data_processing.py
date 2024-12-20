from collections import defaultdict
from itertools import combinations

from oaf.util import validate_check_data, validate_wave_data


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
