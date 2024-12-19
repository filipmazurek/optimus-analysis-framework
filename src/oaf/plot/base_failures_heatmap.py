"""
Base failures: analyze the root cause of node failure for every Optimus triggerred wave.
For every check_data failure, check if the reason it failed is because a calibration this node
depends on failed. If so, attribute the failure to the calibration node. If not, attribute it
to the node itself.
This is useful for identifying the root cause of a failure in a complex system. The root cause
node can then be targeted for more frequent checks and calibrations.
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from oaf.base_failure import calc_base_failure_proportion


def plot_base_failure_heatmap(base_failure_proportions, nodes):
    labels = nodes

    # Create a 2D matrix for the proportions
    heatmap_data = np.zeros((len(labels), len(labels)))

    for x_idx, x_label in enumerate(labels):
        for y_idx, y_label in enumerate(labels):
            heatmap_data[y_idx, x_idx] = base_failure_proportions.get(x_label, {}).get(y_label, 0.0)

    # Plot the heatmap using Seaborn
    plt.figure(figsize=(8, 6))
    ax = sns.heatmap(
        heatmap_data,
        annot=True,  # Annotate cells with data values
        fmt=".2f",  # Format the annotations to 2 decimal places
        # cmap="viridis",  # Color map
        linewidths=0.5,  # Gridline width
        vmin=0, vmax=1,  # Fix legend range from 0 to 1
        cbar_kws={"label": "Proportion"}  # Add a label to the color bar
    )

    # Set axis labels and title
    ax.set_xticks(np.arange(len(nodes)) + 0.5)
    ax.set_yticks(np.arange(len(nodes)) + 0.5)
    ax.set_xticklabels(nodes, rotation=45, ha="right")
    ax.set_yticklabels(nodes)
    ax.set_xlabel("Node Failure")
    ax.set_ylabel("Base Failure")
    ax.set_title("Base Failure Proportions Heatmap")

    # Show the plot
    plt.tight_layout()
    plt.show()


def plot_combined_heatmap(base_failure_counts, nodes):
    """
    Plot a combined heatmap of base failure proportions and raw counts.

    Args:
        base_failure_counts (dict): Raw counts of failures per downstream node.
        nodes (list): List of node labels for X and Y axes.
    """
    # Calculate proportion stats
    base_failure_proportions = calc_base_failure_proportion(base_failure_counts)

    # Create proportion and count matrices
    proportions = np.zeros((len(nodes), len(nodes)))
    counts = np.zeros((len(nodes), len(nodes)))

    for x_idx, x_label in enumerate(nodes):
        for y_idx, y_label in enumerate(nodes):
            proportions[y_idx, x_idx] = base_failure_proportions.get(x_label, {}).get(y_label, 0.0)
            counts[y_idx, x_idx] = base_failure_counts.get(x_label, {}).get(y_label, 0)

    # Plot proportions heatmap
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    sns.heatmap(
        proportions,
        annot=True,
        fmt=".2f",
        cmap="viridis",
        linewidths=0.5,
        vmin=0, vmax=1,
        xticklabels=nodes, yticklabels=nodes,
        cbar_kws={"label": "Proportion"}
    )
    plt.title("Base Failure Proportions")
    plt.xlabel("Node Failure")
    plt.ylabel("Base Failure")

    # Plot counts heatmap
    plt.subplot(1, 2, 2)
    sns.heatmap(
        counts,
        annot=True,
        fmt=".0f",
        cmap="Blues",
        linewidths=0.5,
        xticklabels=nodes, yticklabels=nodes,
        cbar_kws={"label": "Raw Counts"}
    )
    plt.title("Base Failure Raw Counts")
    plt.xlabel("Node Failure")
    plt.ylabel("Base Failure")

    plt.tight_layout()
    plt.show()
