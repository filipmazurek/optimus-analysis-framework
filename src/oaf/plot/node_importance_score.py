import matplotlib.pyplot as plt
import numpy as np

from oaf.data_processing import find_co_occurring_failures
from oaf.base_failure import find_base_failures, find_mean_failure_chain_length
from oaf.util import validate_check_data, validate_wave_data


def calculate_check_scores(wave_data, check_data, graph):
    """
    Calculate 'check more' and 'check less' scores for nodes.
    Give unrefined data to this function so all analysis is completed here.
    'check_more' is typically nodes which fail more often or are the base cause node for many failures.
    Their check data may be drifting more quickly than expected.

    :param wave_data: list of dict: List of wave data information.
    :param check_data: list of dict: List of check data information.
    :param graph: nx.DiGraph: Graph representing node relationships.
    """
    # Assert wave data and check data is correctly formatted
    validate_wave_data(wave_data)
    validate_check_data(check_data)

    wave_data = sorted(wave_data, key=lambda x: x['wave'])

    base_failure_data = find_base_failures(wave_data, graph)

    scores = {}

    node_data = {node: {'checks': 0, 'failures': 0, 'failure_magnitudes': [], 'avg_failure_chain_length': 0,
                        'cofailure_score': 0} for node in graph.nodes}

    # Total data_checks and data_check failures
    for check in check_data:
        if check['check_type'] != 'check_data':
            continue
        node = check['node']
        node_data[node]['checks'] += 1
        if check['failure_magnitude'] > 0:
            node_data[node]['failures'] += 1
            node_data[node]['failure_magnitudes'].append(check['failure_magnitude'])

    # Failure chains
    base_failure_stats = find_base_failures(wave_data, graph)
    avg_failure_chain_lengths = find_mean_failure_chain_length(base_failure_stats, graph)
    nodes = list(graph.nodes)
    for node in nodes:
        node_data[node]['avg_failure_chain_length'] = avg_failure_chain_lengths[node]

    # Co-failure correlation

    # Calculate the co-occuring failures for each wave
    co_occurring_data = find_co_occurring_failures(wave_data, check_data)

    for node in graph.nodes:
        cofailure_score = sum(
            co_occurring_data.get(tuple(sorted((node, other))), 0)
            for other in graph.nodes if other != node
        )
        node_data[node]['cofailure_score'] = cofailure_score

    # Calculate a score for each node
    for node in graph.nodes:
        # Success rate and unnecessary checks
        total_check_count = node_data[node]['checks']
        failure_count = node_data[node]['failures']
        success_rate = (total_check_count - failure_count) / max(1, total_check_count)
        unnecessary_checks = total_check_count - failure_count
        avg_failure_magnitude = sum(node_data[node]['failure_magnitudes']) / max(1, len(node_data[node]['failure_magnitudes']))
        downstream_impact = node_data[node]['avg_failure_chain_length']
        cofailure_score = node_data[node]['cofailure_score']

        # Calculate scores
        check_more_score = (
                4. * avg_failure_magnitude
                + 10 * (1 - success_rate)
                + 10. * downstream_impact
                + 3. * cofailure_score
        )
        check_less_score = (
                0.5 * success_rate
                + 0.2 * (1 / max(1., avg_failure_magnitude))
                + 0.2 * (1 / max(1, downstream_impact))
        )

        scores[node] = {
            'check_more': check_more_score,
            'check_less': check_less_score
        }

    return scores


def plot_check_scores(check_scores, nodes):
    """
    Plot bar chart with both 'check more' and 'check less' scores for each node.

    :param check_scores: dict: Dictionary of check scores for each node.
    :param nodes: list: List of all nodes in the order to be displayed.
    """
    check_more_scores = [check_scores[node]['check_more'] for node in nodes]
    check_less_scores = [check_scores[node]['check_less'] for node in nodes]

    fig, ax = plt.subplots(figsize=(12, 6))
    bar_width = 0.35
    index = np.arange(len(nodes))

    ax.bar(index, check_more_scores, bar_width, label='Check More')
    ax.bar(index + bar_width, check_less_scores, bar_width, label='Check Less', color='r')

    ax.set_xlabel('Nodes')
    ax.set_ylabel('Check Scores')
    ax.set_title('Check Scores for Nodes')
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(nodes, rotation=45, ha='right')
    ax.legend()

    plt.tight_layout()
    plt.show()
