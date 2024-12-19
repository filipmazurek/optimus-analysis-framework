import networkx as nx
import matplotlib.pyplot as plt

from oaf.data_processing import split_data_by_wave
from oaf.util import validate_wave_data

def _plot_wave(node_graph, trigger_wave=True, checked_nodes=None, failed_nodes=None, wave_value=None, filename=None):
    if checked_nodes is None:
        checked_nodes = []
    if failed_nodes is None:
        failed_nodes = []

    # Precompute the layout for consistent positioning
    pos = nx.spring_layout(node_graph, seed=1)  # Use a fixed seed for reproducibility

    # Adjust checked color based on trigger status
    if trigger_wave:
        checked_color = "tab:blue"
    else:
        checked_color = "tab:green"

    # Assign colors based on node status
    node_colors = []
    for node in node_graph.nodes:
        if node in failed_nodes:
            node_colors.append("tab:red")  # Failed
        elif node in checked_nodes:
            node_colors.append(checked_color)  # Checked
        else:
            node_colors.append("whitesmoke")  # Not active in this wave

    # Create title
    if trigger_wave:
        title = f'Trigger Wave {wave_value}'
    else:
        title = f'Diagnosis Wave {wave_value}'

    # Draw the graph with fixed positions
    plt.figure(figsize=(10, 6))
    plt.title(title)
    nx.draw(
        node_graph,
        pos,  # Use the fixed layout
        with_labels=True,
        node_color=node_colors,
        node_size=800,
        font_size=10,
    )

    if filename is not None:
        plt.savefig(filename)
    else:
        plt.show()


def _process_wave(data, graph):
    checked_nodes = set()

    # Separate data into the regular maintain wave and the diagnosis waves
    maintain_event = data[0]  # Assume the first event is the maintain wave
    diagnosis_data = [event for event in data if not event["timed_trigger"]]

    # Maintain wave
    # Get all checked nodes
    checked_nodes.update(maintain_event["submitted_nodes"])

    # _create_graph(node_graph, checked_nodes, trigger_wave=True, wave_value=maintain_event["wave"])
    trigger_event_data = {'checked_nodes': checked_nodes, 'wave_value': maintain_event["wave"]}

    # Check if there is any diagnosis data
    if not diagnosis_data:
        return trigger_event_data, None

    # Reset sets
    checked_nodes = set()
    failed_nodes = set()
    propagation_edges = set()

    # Diagnosis waves
    for event in diagnosis_data:
        # Get all checked nodes
        checked_nodes.update(event["submitted_nodes"])

        # Get all failed nodes
        failed_nodes.update(event["root_nodes"])
        propagation_edges.update((root, node) for root in event["root_nodes"] for node in event["submitted_nodes"])

    # If a node both checked and failed, failure takes precedence
    checked_nodes -= failed_nodes

    # _create_graph(node_graph, checked_nodes, failed_nodes, trigger_wave=False, wave_value=maintain_event["wave"])
    diagnosis_wave_data = {'checked_nodes': checked_nodes, 'failed_nodes': failed_nodes, 'wave_value': maintain_event["wave"]}

    return trigger_event_data, diagnosis_wave_data


def plot(data: list[list[dict]], node_graph: nx.digraph, filenames: list[list[str]]=None):
    """
    Visualize each wave of the Optimus algorithm. For every triggered wave, there will be two plots.
    The first plot shows the nodes that were submitted due to a timeout and the propagated
    results of check_state.
    The second plot shows the node diagnosis wave, where the nodes that failed check_data are submitted.

    :param data: prepared list of wave data events
    :type data: list of list of dict
    :param node_graph: nx digraph of node relationships.
    :type node_graph: nx.DiGraph
    :param filenames: list of lists of filenames for saving plots. Each sublist contains a filename for the maintain
      wave and a filename for the diagnosis wave.
    """
    # Validate input data
    for wave in data:
        validate_wave_data(wave)

    if filenames is not None:
        assert 2 * len(data) == len(filenames), "Number of data sets must match number of filenames"
    else:
        filenames = [[None, None]] * len(data)

    # Process and plot each wave
    for i, wave_data in enumerate(data):
        trigger_event_data, diagnostic_wave_data = _process_wave(wave_data, node_graph)
        _plot_wave(node_graph, trigger_wave=True, filename=filenames[i][0], **trigger_event_data)
        if diagnostic_wave_data is not None:
            _plot_wave(node_graph, trigger_wave=False, filename=filenames[i][1], **diagnostic_wave_data)

def prep_data(data):
    """
    Transform a list of `wave` data events into a format taken by the plotting function.

    :param data: List of `wave` events
    :type data: list of dict
    """
    return split_data_by_wave(data)
