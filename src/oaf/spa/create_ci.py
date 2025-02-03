import networkx as nx
from spa.core import spa
from spa.properties import ThresholdProperty
from spa.util import min_num_samples

from oaf.data_processing import count_failures, count_base_failures, time_to_failure, time_to_failure_base


def ci_for_parameter(parameter, proportion=0.9, confidence=0.9):
    """
    Calculate a confidence interval for a given parameter.

    :param parameter: list[float]: The parameter values.
    :param proportion: float: Proportion for SPA
    :param confidence: float: Confidence level for the interval.
    :return: tuple[float]: The lower and upper bounds of the CI.
    """
    return spa(ThresholdProperty(), parameter, proportion, confidence)


def _ci_time_to_failure(failure_type, wave_data, graph, proportion=0.9, confidence=0.9):
    # Check what type of failure the function is counting
    if failure_type == 'all':
        count_func = time_to_failure
    elif failure_type == 'base':
        count_func = time_to_failure_base
    else:
        raise ValueError(f'Invalid failure type: {failure_type}')

    # Get times to failure for each node
    times_to_failure = count_func(wave_data, nodes)

    # Calculate the CI for each node that has enough samples
    ci = {}
    for node in nodes:
        if len(times_to_failure[node]) >= min_num_samples(proportion, confidence):
            ci[node] = spa(ThresholdProperty(), times_to_failure[node], proportion, confidence)
        else:
            ci[node] = None

    return ci


def ci_time_to_failure(wave_data, graph, proportion=0.9, confidence=0.9):
    """
    Calculate a confidence interval for the time to failure for all failures for each node.

    :param wave_data: list[dict]: The wave data.
    :param graph: nx.DiGraph: The graph representing node relationships.
    :param proportion: float: Proportion for SPA
    :param confidence: float: Confidence level for the interval.
    :return: dict: A dictionary where keys are nodes and values are tuples of the lower and upper bounds of the CI.
    """
    _ci_time_to_failure('all', wave_data, nodes, proportion, confidence)


def ci_time_to_failure_base(wave_data, graph, proportion=0.9, confidence=0.9):
    """
    Calculate a confidence interval for the time to failure for base failures for each node.

    :param wave_data: list[dict]: The wave data.
    :param graph: nx.DiGraph: The graph representing node relationships.
    :param proportion: float: Proportion for SPA
    :param confidence: float: Confidence level for the interval
    :return: dict: A dictionary where keys are nodes and values are tuples of the lower and upper bounds of the CI.
    """
    _ci_time_to_failure('base', wave_data, nodes, proportion, confidence)


def _ci_for_failures_in_time_period(failure_type, node_failure_counts, nodes, proportion=0.9, confidence=0.9):
    # Check what type of failure the function is counting
    if failure_type == 'all':
        count_func = count_failures
    elif failure_type == 'base':
        count_func = count_base_failures
    else:
        raise ValueError(f'Invalid failure type: {failure_type}')

    # Ensure there are enough samples for SPA
    assert len(node_failure_counts) >= min_num_samples(proportion, confidence), \
        (f'Given proportion={proportion} and confidence={confidence}, '
         f'SPA requires at least {min_num_samples(proportion, confidence)} samples.')

    # Count the number of failures per node for each time period
    node_failures = {node: [] for node in nodes}
    for time_period in node_failure_counts:
        node_failures_in_wave = count_func(time_period, nodes)
        for node in nodes:
            node_failures[node].append(node_failures_in_wave[node])

    # Calculate the CI for each node
    ci = {}

    for node in nodes:
        ci[node] = spa(ThresholdProperty(), node_failures[node], proportion, confidence)

    return ci


def ci_failures_per_time_period(node_failure_counts, nodes, proportion=0.9, confidence=0.9):
    """
    Calculate a confidence interval for the number of failures per node in a given time period.
    This is for all failures, not just base failures.

    :param node_failure_counts: list[list[dict]]: Per-wave data for multiple time periods. Each list is a time period.
    :param nodes: list[str]: The nodes for which to calculate the CI.
    :param proportion: float: Proportion for SPA
    :param confidence: float: Confidence level for the interval.
    :return: dict: A dictionary where keys are nodes and values are tuples of the lower and upper bounds of the CI.
    """
    return _ci_for_failures_in_time_period('all', node_failure_counts, nodes, proportion, confidence)


def ci_failures_base_per_time_period(node_failure_counts, nodes, proportion=0.9, confidence=0.9):
    """
    Calculate a confidence interval for the number of base failures per node in a given time period.

    :param node_failure_counts: list[list[dict]]: Per-wave data for multiple time periods. Each list is a time period.
    :param nodes: list[str]: The nodes for which to calculate the CI.
    :param proportion: float: Proportion for SPA
    :param confidence: float: Confidence level for the interval.
    """
    return _ci_for_failures_in_time_period('base', node_failure_counts, nodes, proportion, confidence)
