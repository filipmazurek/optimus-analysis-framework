import matplotlib.pyplot as plt
import numpy as np

def plot(ci_per_node, filename=None, failure_type='all', specific_title='', time_units='Arbitrary Units'):
    """
    Plot the confidence intervals for time to failure for each node.

    :param ci_per_node: dict: A dictionary where keys are nodes and values are tuples of the lower and upper bounds of the CI.
    """

    # NOTE: use an OrderedDict for ci_per_node to preserve the order of nodes in the plot

    if specific_title != '' and failure_type == 'base':
        specific_title = f', {specific_title}'

    if failure_type == 'all':
        title = f'Time to Failure CI\n{specific_title}'
    elif failure_type == 'base':
        title = f'Time to Failure CI\nBase Failures{specific_title}'
    else:
        raise ValueError(f'Invalid failure type: {failure_type}')

    # Convert node names to numeric indices for plotting
    nodes = list(ci_per_node.keys())
    y_positions = np.arange(len(nodes))  # Numeric indices for y-axis

    # Extract lower and upper bounds
    ci_lows = np.array([ci[0] if ci else np.nan for ci in ci_per_node.values()])
    ci_highs = np.array([ci[1] if ci else np.nan for ci in ci_per_node.values()])

    # Compute error bars
    errors = [(ci_highs - ci_lows) / 2]  # Half CI width

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 6))

    # Plot error bars (horizontal, indexed by y_positions)
    ax.errorbar(
        x=(ci_lows + ci_highs) / 2, y=y_positions,
        xerr=errors, fmt='o', color='skyblue', capsize=5, capthick=2
    )

    # Set labels and title
    ax.set_xlabel(f'Time ({time_units})')
    ax.set_ylabel('Node')
    ax.set_title(title)

    # Map numeric indices back to node names
    ax.set_yticks(y_positions)
    ax.set_yticklabels(nodes)

    # Expand x-axis limits slightly for clarity
    ax.set_xlim(np.nanmin(ci_lows) * 0.9, np.nanmax(ci_highs) * 1.1)

    # Annotate actual values
    for i, (low, high) in enumerate(zip(ci_lows, ci_highs)):
        ax.text(low, i, f"{low:.3g}", va='center', ha='right', fontsize=10, color="red")
        ax.text(high, i, f"{high:.3g}", va='center', ha='left', fontsize=10, color="red")

    # Improve layout
    plt.xticks(rotation=30)
    plt.grid(True, which="both", linestyle="--", alpha=0.6)
    plt.tight_layout(pad=2)

    # Save or show the plot
    if filename:
        plt.savefig(filename, bbox_inches="tight")
    else:
        plt.show()


# Example usage
if __name__ == '__main__':
    ci_data = {
        'A': (3.3, 4.3),
        'B': (0.994, 0.996),
        'C': (1.1, 1.2),
        'D': (0.9, 1.1),
    }

    plot(ci_data, failure_type='all')
