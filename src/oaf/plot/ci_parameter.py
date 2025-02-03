import matplotlib.pyplot as plt
import numpy as np


def plot(ci_per_parameter, filename=None):
    """
    Plots normalized confidence intervals for multiple parameters using a log scale.
    The plot centers all CIs around 0 for easy comparison, while still labeling actual values.

    :param ci_per_parameter: dict: A dictionary where keys are parameters and values are tuples of the lower and upper bounds of the CI.
    """
    parameters = list(ci_per_parameter.keys())
    ci_lows = np.array([ci[0] for ci in ci_per_parameter.values()])
    ci_highs = np.array([ci[1] for ci in ci_per_parameter.values()])

    # Compute means and normalized errors
    means = (ci_lows + ci_highs) / 2  # Mean of each CI
    errors = (ci_highs - ci_lows) / 2  # Half CI width

    # Normalize: Center all intervals at 0
    normalized_lows = (ci_lows - means) / means
    normalized_highs = (ci_highs - means) / means

    # Assign integer indices for plotting
    y_positions = np.arange(len(parameters))

    fig, ax = plt.subplots(figsize=(8, 6))

    # Plot error bars centered at 0, using integer indices for y-axis
    ax.errorbar(
        np.zeros_like(y_positions), y_positions,
        xerr=[-normalized_lows, normalized_highs], fmt='o', capsize=5, capthick=2, color='blue'
    )

    # Set log scale for x-axis
    ax.set_xscale('symlog')
    ax.set_xlabel('Normalized Confidence Interval (Centered at 0)')
    ax.set_title('Normalized Confidence Intervals for Specified Parameters')

    # Set y-ticks to parameter names
    ax.set_yticks(y_positions)
    ax.set_yticklabels(parameters)

    # Adjust layout
    plt.grid(True, which='both', linestyle='--', alpha=0.6)
    plt.tight_layout()

    # Save or show the plot
    if filename:
        plt.savefig(filename)
    else:
        plt.show()


if __name__ == '__main__':
    # Example usage
    ci_data = {
        'Init Time (µs)': (48, 50),
        'Dark Fidelity': (0.994, 0.996),
        'Laser Frequency (Hz)': (3.5e9, 3.51e9),
        'Microwave Amplitude': (0.9, 1.1),
    }

    plot(ci_data)
