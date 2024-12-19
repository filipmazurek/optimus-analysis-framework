from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np

from oaf.util import validate_check_data


def plot(check_data, nodes, include_passes=True, filename=None):
    """
    For every check_data, aggregate the failure magnitude of the check. Visualize the
    failure magnitudes by node in a stacked bar chart.
    This analysis is useful for identifying the proportion of severe failures for every node.
    This analysis has the option to check only failures (magnitude > 0) or all checks.

    :param check_data: list of dict: List of failure data dictionaries.
    :param nodes: list: List of node labels.
    :param include_passes: bool: Include passes in the visualization.
    :param filename: str: File path to save the plot.
    """
    validate_check_data(check_data)

    # Prepare data for visualization
    magnitude_0 = defaultdict(int)
    magnitude_1 = defaultdict(int)
    magnitude_2 = defaultdict(int)

    for entry in check_data:
        # Only check entries that are of type 'check_data'
        if entry['check_type'] != 'check_data':
            continue
        node = entry['node']
        if entry['failure_magnitude'] == 0:
            magnitude_0[node] += 1
        if entry['failure_magnitude'] == 1:
            magnitude_1[node] += 1
        elif entry['failure_magnitude'] == 2:
            magnitude_2[node] += 1

    # Get node values
    mag0_values = [magnitude_0[node] for node in nodes]
    mag1_values = [magnitude_1[node] for node in nodes]
    mag2_values = [magnitude_2[node] for node in nodes]

    # Plotting
    fig, ax = plt.subplots(figsize=(8, 6))

    # Create stacked bar chart
    bar_width = 0.6
    if include_passes:
        bottom = np.zeros(len(nodes))
        ax.bar(nodes, mag0_values, bottom=bottom, label='Pass', color='lightgreen', width=bar_width)
        bottom += np.array(mag0_values)
        ax.bar(nodes, mag1_values, bottom=bottom, label='Magnitude 1 Failures', color='skyblue', width=bar_width)
        bottom += np.array(mag1_values)
        ax.bar(nodes, mag2_values, bottom=bottom, label='Magnitude 2 Failures', color='salmon', width=bar_width)

    # Set the y-axis to only use integer ticks
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Add labels, legend, and title
    ax.set_xlabel('Nodes', fontsize=12)
    if include_passes:
        ax.set_ylabel('Number of Checks', fontsize=12)
        ax.set_title('Check Data by Node', fontsize=14)
    else:
        ax.set_ylabel('Number of Failures', fontsize=12)
        ax.set_title('Failure Magnitudes by Node', fontsize=14)
    ax.legend()

    # Show grid and plot
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    if filename is not None:
        plt.savefig(filename)
    else:
        plt.show()
