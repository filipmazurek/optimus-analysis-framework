"""
Calculates the co-occuring failures for each wave in Optimus. When multiple nodes continually fail
together there may be a strong relationship between them that is not captured by the Optimus DAG.
This analysis can identify which nodes are likely to fail together and may require more frequent checks.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def plot(cooccurring_data, all_nodes, filename=None):
    """
    Plot a heatmap of co-occurring failures for nodes using Seaborn.

    :param cooccurring_data: dict: Co-occurrence matrix {node_pair: count}.
    :param all_nodes: list: List of all nodes involved in the simulation.
    """
    # Create a mapping of node names to indices
    node_index = {node: i for i, node in enumerate(all_nodes)}

    # Initialize a square DataFrame for the heatmap
    size = len(all_nodes)
    heatmap = pd.DataFrame(np.zeros((size, size)), index=all_nodes, columns=all_nodes)

    # Populate the heatmap with co-occurrence counts
    for (node1, node2), count in cooccurring_data.items():
        # heatmap.loc[node1, node2] = count
        heatmap.loc[node2, node1] = count

    # Get the Upper Triangle of the co-relation matrix
    corr = heatmap.corr()
    matrix = np.triu(corr)

    # Plot the heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        heatmap,
        annot=True,
        fmt=".0f",
        # cmap="coolwarm",
        cbar_kws={"label": "Co-Occurrence Count"},
        linewidths=0.5,
        linecolor="gray",
        mask=matrix  # Use the upper triangle matrix as mask
    )
    plt.title("Co-Occurring Failures Heatmap", pad=20)
    plt.xlabel("Nodes")
    plt.ylabel("Nodes")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()

    if filename is not None:
        plt.savefig(filename)
    else:
        plt.show()
