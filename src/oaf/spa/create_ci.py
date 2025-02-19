import networkx as nx
from spa.core import spa
from spa.properties import ThresholdProperty
from spa.util import min_num_samples

from oaf.data_analysis import count_failures, count_base_failures, time_to_failure, time_to_failure_base


def ci_for_parameter(parameter, proportion, confidence):
    """
    Calculate a confidence interval for a given parameter.

    :param parameter: list[float]: The parameter values.
    :param proportion: float: Proportion for SPA
    :param confidence: float: Confidence level for the interval.
    :return: tuple[float]: The lower and upper bounds of the CI.
    """
    return spa(parameter, ThresholdProperty(), proportion, confidence)


def ci_time_to_failure(times_to_failure, proportion, confidence):
    """
    Create SPA confidence intervals for the time to failure for each node.
    """
    nodes = times_to_failure.keys()

    # Calculate the CI for each node that has enough samples
    ci = {}
    for node in nodes:
        if len(times_to_failure[node]) >= min_num_samples(proportion, confidence):
            spa_result = spa(times_to_failure[node], ThresholdProperty(), proportion, confidence)
            ci[node] = (spa_result.confidence_interval.low, spa_result.confidence_interval.high)
        else:
            ci[node] = None

    return ci


def _ci_time_to_failure_wave_data(failure_type, wave_data, graph, proportion, confidence):
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
            ci[node] = spa(times_to_failure[node], ThresholdProperty(), proportion, confidence)
        else:
            ci[node] = None

    return ci


def ci_time_to_failure_wave_data(wave_data, graph, proportion, confidence):
    """
    Calculate a confidence interval for the time to failure for all failures for each node.

    :param wave_data: list[dict]: The wave data.
    :param graph: nx.DiGraph: The graph representing node relationships.
    :param proportion: float: Proportion for SPA
    :param confidence: float: Confidence level for the interval.
    :return: dict: A dictionary where keys are nodes and values are tuples of the lower and upper bounds of the CI.
    """
    _ci_time_to_failure_wave_data('all', wave_data, nodes, proportion, confidence)


def ci_time_to_failure_base_wave_data(wave_data, graph, proportion, confidence):
    """
    Calculate a confidence interval for the time to failure for base failures for each node.

    :param wave_data: list[dict]: The wave data.
    :param graph: nx.DiGraph: The graph representing node relationships.
    :param proportion: float: Proportion for SPA
    :param confidence: float: Confidence level for the interval
    :return: dict: A dictionary where keys are nodes and values are tuples of the lower and upper bounds of the CI.
    """
    _ci_time_to_failure_wave_data('base', wave_data, nodes, proportion, confidence)


def _ci_for_failures_in_time_period(failure_type, list_of_wave_data_lists, graph, proportion, confidence):
    nodes = graph.nodes
    # Check what type of failure the function is counting
    if failure_type == 'all':
        count_func = count_failures
    elif failure_type == 'base':
        count_func = count_base_failures
    else:
        raise ValueError(f'Invalid failure type: {failure_type}')

    # Ensure there are enough samples for SPA
    assert len(list_of_wave_data_lists) >= min_num_samples(proportion, confidence), \
        (f'Given proportion={proportion} and confidence={confidence}, '
         f'SPA requires at least {min_num_samples(proportion, confidence)} samples.')

    # Count the number of failures per node for each time period
    node_failures = {node: [] for node in nodes}
    for time_period in list_of_wave_data_lists:
        node_failures_in_wave = count_func(time_period, graph)
        for node in nodes:
            node_failures[node].append(node_failures_in_wave[node])

    # Calculate the CI for each node
    ci = {}

    for node in nodes:
        if len(node_failures[node]) >= min_num_samples(proportion, confidence):
            spa_result = spa(node_failures[node], ThresholdProperty(), proportion, confidence)
            if spa_result.confidence_interval is None:
                ci[node] = None
            else:
                ci[node] = (spa_result.confidence_interval.low, spa_result.confidence_interval.high)
        else:
            ci[node] = None

    return ci


def ci_failures_per_time_period(list_of_wave_data_list, graph, proportion, confidence):
    """
    Calculate a confidence interval for the number of failures per node in a given time period.
    This is for all failures, not just base failures.

    :param list_of_wave_data_list: list[list[dict]]: Per-wave data for multiple time periods. Each list is a time period.
    :param graph: nx.Digraph: The graph representing node relationships.
    :param proportion: float: Proportion for SPA
    :param confidence: float: Confidence level for the interval.
    :return: dict: A dictionary where keys are nodes and values are tuples of the lower and upper bounds of the CI.
    """
    return _ci_for_failures_in_time_period('all', list_of_wave_data_list, graph, proportion, confidence)


def ci_failures_base_per_time_period(node_failure_counts, graph, proportion, confidence):
    """
    Calculate a confidence interval for the number of base failures per node in a given time period.

    :param node_failure_counts: list[list[dict]]: Per-wave data for multiple time periods. Each list is a time period.
    :param graph: nx.Digraph: The graph representing node relationships.
    :param proportion: float: Proportion for SPA
    :param confidence: float: Confidence level for the interval.
    """
    return _ci_for_failures_in_time_period('base', node_failure_counts, graph, proportion, confidence)
