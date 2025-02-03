from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from oaf.util import validate_wave_data


def calculate_time_to_failure(wave_data, nodes):
    """
    Calculate the time to failure for each node.

    :param wave_data: list of dict: List of wave data dicts
    :param nodes: list of str: List of node names
    :return: dict: {node: [time_to_failure]} where each value is a list of intervals between failures.
    """
    validate_wave_data(wave_data)

    time_to_failure = {node: [] for node in nodes}
    last_fail_time = {}

    for entry in wave_data:
        # Skip timed triggers, as they are not failures
        if entry['timed_trigger']:
            continue
        # Any diagnosis wave root nodes are failures
        # TODO: this is unnecessary
        assert len(entry['root_nodes']) == 1, "Multiple root nodes in a diagnosis wave."
        node = entry['root_nodes'][0]
        wave = entry['wave']

        if node in last_fail_time:
            # Record the time since the last successful calibration or start
            time_to_failure[node].append(wave - last_fail_time[node])
        # Update the last check time to the failure wave
        last_fail_time[node] = wave

    return time_to_failure


def plot(time_to_failure, filename=None):
    """
    Plot a horizontal box-and-whisker plot for time to failure alongside a bar graph for failure counts.

    :param time_to_failure: dict: {node: [time_to_failure]} for each node.
    """
    # Assert that time_to_failure is a correctly formatted dict
    assert all(isinstance(node, str) and isinstance(intervals, list) for node, intervals in time_to_failure.items()), \
        "Invalid time_to_failure format."


    # Prepare data for plotting
    nodes = []
    times = []
    num_failures = {node: len(intervals) for node, intervals in time_to_failure.items()}

    for node, intervals in time_to_failure.items():
        if intervals:  # Include only nodes with failures in the times list
            nodes.extend([node] * len(intervals))
            times.extend(intervals)
        else:
            # Add a placeholder entry for nodes without failures
            nodes.append(node)
            times.append(None)

    failure_counts = [len(intervals) for time_to_failure in times]

    # Create a DataFrame for Seaborn
    data = pd.DataFrame({'Node': nodes, 'Time to Failure': times})

    # Create side-by-side plots
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={'width_ratios': [2, 1]})

    # Plot the box-and-whisker plot
    sns.boxplot(
        data=data,
        y='Node',
        x='Time to Failure',
        ax=axes[0],
        showmeans=True,
        meanline=True,
        meanprops={"color": "black", "ls": "-", "lw": 1.5}
    )
    axes[0].set_title('Time to Failure for Nodes')
    axes[0].set_xlabel('Time to Failure (time units)')
    axes[0].set_ylabel('Node')

    # Plot the bar graph for failure counts
    axes[1].barh(num_failures.keys(), num_failures.values(), color='gray', alpha=0.7)
    axes[1].set_title('Failure Count for Nodes')
    axes[1].set_xlabel('Failure Count')
    axes[1].set_yticks(range(len(nodes)))
    axes[1].set_yticklabels(nodes)
    axes[1].set_ylim(axes[0].get_ylim())  # Align Y-axis with the boxplot

    # Adjust layout
    plt.tight_layout()
    if filename is not None:
        plt.savefig(filename)
    else:
        plt.show()


def plot_only_box_and_whisker(time_to_failure, filename=None):
    """
    Plot a horizontal box-and-whisker plot for time to failure for each node.
    Nodes without failures will appear without lines.

    :param time_to_failure: dict: {node: [time_to_failure]} for each node.
    """
    # Prepare data for plotting
    nodes = []
    times = []

    for node, intervals in time_to_failure.items():
        if intervals:  # Include only nodes with failures in the times list
            nodes.extend([node] * len(intervals))
            times.extend(intervals)
        else:
            # Add a placeholder entry for nodes without failures
            nodes.append(node)
            times.append(None)

    # Create a DataFrame for Seaborn
    data = pd.DataFrame({'Node': nodes, 'Time to Failure': times})

    # Plot using Seaborn
    plt.figure(figsize=(10, 6))
    sns.boxplot(
        data=data,
        y='Node',  # Horizontal orientation
        x='Time to Failure',
        showmeans=True,
        meanline=True,
        meanprops={"color": "black", "ls": "-", "lw": 1.5}
    )
    plt.title('Time to Failure for Nodes')
    plt.ylabel('Node')
    plt.xlabel('Time to Failure (time units)')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()

    if filename is not None:
        plt.savefig(filename)
    else:
        plt.show()

