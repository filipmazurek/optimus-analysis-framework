import networkx as nx

from oaf.optimus_simulator.calibration_simulator import QuantumCalibrationSimulator
from oaf.optimus_simulator.comparison_funcs import create_spa_greater_than, mean_greater_than
from oaf.optimus_simulator.node import SimpleNode, TrendNode, DistributionThresholdNode


def simple_sim1():
    # Create a graph representing C -> B -> A
    graph = nx.DiGraph()
    # Add nodes in recursive dfs order (deepest to shallowest). This will simulate the
    #   recursive visits of the wave algorithm
    graph.add_nodes_from(['A', 'B', 'C'])
    graph.add_edges_from([('C', 'B'), ('B', 'A')])

    # Create the nodes
    nodes = {
        'A': SimpleNode(name='A', timeout=5, failure_prob=0.1),
        'B': SimpleNode(name='B', timeout=3, failure_prob=0.2),
        'C': SimpleNode(name='C', timeout=7, failure_prob=0.3)
    }

    # Initialize the simulator
    simulator = QuantumCalibrationSimulator(graph, nodes=nodes, root_nodes=['C'], time_step=1, timeout=1)

    return graph, nodes, simulator


def simple_sim2():
    # Create a graph representing C -> B -> A
    #                             E -> D /
    graph = nx.DiGraph()
    # Add nodes in recursive dfs order (deepest to shallowest). This will simulate the
    #   recursive visits of the wave algorithm
    graph.add_nodes_from(['A', 'B', 'C', 'D', 'E'])
    graph.add_edges_from([('C', 'B'), ('B', 'A'), ('E', 'D'), ('D', 'A')])

    # Create the nodes
    nodes = {
        'A': SimpleNode(name='A', timeout=5, failure_prob=0.05),
        'B': SimpleNode(name='B', timeout=3, failure_prob=0.1),
        'C': SimpleNode(name='C', timeout=7, failure_prob=0.2),
        'D': SimpleNode(name='D', timeout=4, failure_prob=0.1),
        'E': SimpleNode(name='E', timeout=7, failure_prob=0.2)
    }

    # Initialize the simulator
    simulator = QuantumCalibrationSimulator(graph, nodes=nodes, root_nodes=['C', 'E'], time_step=1, timeout=1)

    return graph, nodes, simulator


def trend_sim_1():
    # Create a graph representing C -> B -> A
    graph = nx.DiGraph()
    # Add nodes in recursive dfs order (deepest to shallowest). This will simulate the
    #   recursive visits of the wave algorithm
    graph.add_nodes_from(['A', 'B', 'C'])
    graph.add_edges_from([('C', 'B'), ('B', 'A')])

    # Create the nodes
    nodes = {
        'A': TrendNode(name='A', timeout=2, initial_value=0., drift_rate=0.1, noise_std=0.1, threshold=0.5),
        'B': TrendNode(name='B', timeout=2, initial_value=0., drift_rate=0.1, noise_std=0.1, threshold=0.5),
        'C': TrendNode(name='C', timeout=1, initial_value=0., drift_rate=0.1, noise_std=0.1, threshold=0.1)
    }

    # Initialize the simulator
    simulator = QuantumCalibrationSimulator(graph, nodes=nodes, root_nodes=['C'], time_step=1, timeout=1)

    return graph, nodes, simulator


def threshold_sim_1():
    # Create a graph representing C -> B -> A
    graph = nx.DiGraph()
    # Add nodes in recursive dfs order (deepest to shallowest). This will simulate the
    #   recursive visits of the wave algorithm
    graph.add_nodes_from(['A', 'B', 'C'])
    graph.add_edges_from([('C', 'B'), ('B', 'A')])

    # Create the nodes
    nodes = {
        'A': DistributionThresholdNode(name='A', timeout=2, dist_type='normal', dist_mean=0., dist_std=0.1, num_samples=1, threshold=0.2, comparison_func=lambda x, y: x[0] > y),
        'B': DistributionThresholdNode(name='B', timeout=2, dist_type='normal', dist_mean=0., dist_std=0.1, num_samples=1, threshold=0.2, comparison_func=lambda x, y: x[0] > y),
        'C': DistributionThresholdNode(name='C', timeout=1, dist_type='normal', dist_mean=0., dist_std=0.1, num_samples=1, threshold=0.2, comparison_func=lambda x, y: x[0] > y)
    }

    # Initialize the simulator
    simulator = QuantumCalibrationSimulator(graph, nodes=nodes, root_nodes=['C'], time_step=1, timeout=1)

    return graph, nodes, simulator


def spa_threshold_sim_1():
    # Create a graph representing C -> B -> A
    graph = nx.DiGraph()
    # Add nodes in recursive dfs order (deepest to shallowest). This will simulate the
    #   recursive visits of the wave algorithm
    graph.add_nodes_from(['A', 'B', 'C'])
    graph.add_edges_from([('C', 'B'), ('B', 'A')])

    spa_proportion = 0.9
    spa_confidence = 0.9
    comparison_func = create_spa_greater_than(spa_proportion, spa_confidence)

    # Create the nodes
    nodes = {
        'A': DistributionThresholdNode(name='A', timeout=2, dist_type='normal', dist_mean=0., dist_std=0.1, num_samples=1, threshold=0.2, comparison_func=comparison_func),
        'B': DistributionThresholdNode(name='B', timeout=2, dist_type='normal', dist_mean=0., dist_std=0.1, num_samples=1, threshold=0.2, comparison_func=comparison_func),
        'C': DistributionThresholdNode(name='C', timeout=1, dist_type='normal', dist_mean=0., dist_std=0.1, num_samples=1, threshold=0.2, comparison_func=comparison_func)
    }

    # Initialize the simulator
    simulator = QuantumCalibrationSimulator(graph, nodes=nodes, root_nodes=['C'], time_step=1, timeout=1)

    return graph, nodes, simulator


if __name__ == '__main__':
    graph, nodes, simulator = simple_sim2()

    # Run the simulation
    simulator.simulate(total_time_steps=10)

    # Retrieve simulation data
    wave_data = simulator.get_wave_data()
    check_data_results = simulator.get_check_data_results()
    ground_truth = simulator.get_ground_truth()

    # Sort the simulation data by wave
    wave_data.sort(key=lambda x: x['wave'])
    check_data_results.sort(key=lambda x: x['wave'])

    # Print simulation data
    print("\n=== Simulation Data ===")
    for wave in wave_data:
        print(wave)

    print("\n=== Check Data Results ===")
    for check_data_result in check_data_results:
        print(check_data_result)

    print("\n=== Ground Truth ===")
    for gt in ground_truth:
        print(gt)

    # Ideally, this data would be saved to a file for further analysis
