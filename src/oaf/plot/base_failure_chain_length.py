import matplotlib.pyplot as plt


def plot(average_chain_lengths_per_node, filename=None):
    """
    Plot the mean failure chain lengths for each node.
    A companion to the base_failures_heatmap. Shows the length of the average failure chain for each node.
    A failure chain of length > 0 indicates that failures propagate from the base node to downstream nodes.
    This analysis can identify which nodes cause lengthy failure chains and may require more frequent checks.

    :param nodes: list: A list of nodes in the graph.
    :param average_chain_lengths_per_node: dict: A list of nodes and their average failure chain lengths
    """
    nodes = list(average_chain_lengths_per_node.keys())
    average_chain_lengths_per_node = list(average_chain_lengths_per_node.values())

    # Plot the average chain lengths as a bar chart
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(nodes, average_chain_lengths_per_node, color='skyblue')
    ax.set_ylim(bottom=0)
    ax.set_xlabel('Base Node')
    ax.set_ylabel('Average Failure Chain Length')
    ax.set_title('Average Failure Chain Length by Base Node')
    plt.xticks(rotation=45)
    plt.tight_layout()

    if filename:
        plt.savefig(filename)
    else:
        plt.show()
