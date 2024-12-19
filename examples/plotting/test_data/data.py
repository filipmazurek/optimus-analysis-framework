import networkx as nx


def fetch_manual_data(index):
    """Fetch manually created data. Gives a list of events and the node graph."""
    node_graph = nx.DiGraph()

    if index == 1:
        # C -> B -> A
        sim_data = [
            # C is always the root. C timed out, but nodes are submitted in recursive DFS order
            {'wave': 1.000, 'timed_trigger': True, 'root_nodes': ['C'], 'submitted_nodes': ['A', 'B', 'C']},
            # A and B have check_state=False, so they do not even run check_data. C failed.
            #   This starts a new wave with depth 1 force submission.
            {'wave': 1.001, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
            # B failed, so A is submitted. Same as the previous
            {'wave': 1.002, 'timed_trigger': False, 'root_nodes': ['B'], 'submitted_nodes': ['A']},
            # C is the most downstream node. It is the 'root' node as defined by the DAX implementation of Optimus
            #   This case assumes that A timed out. A depends on nothing, so only A is submitted.
            {'wave': 2.000, 'timed_trigger': True, 'root_nodes': ['C'], 'submitted_nodes': ['A']}
        ]
        check_data_results = [
            {'wave': 1.001, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 1},
            {'wave': 1.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 1},
            {'wave': 1.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0},
        ]

        # Create a networkx digraph of the relationship C -> B -> A
        node_graph.add_nodes_from(['A', 'B', 'C'])
        node_graph.add_edges_from([('C', 'B'), ('B', 'A')])

    elif index == 2:
        # C -> B -> A
        sim_data = [
            # C is the root. B timed out. nodes are submitted in recursive DFS order from B to the base node A
            {'wave': 1.000, 'timed_trigger': True, 'root_nodes': ['C'], 'submitted_nodes': ['A', 'B']},
            # A had check_state=False, so it did not even run check_data. B ran check_data and failed.
            #   The diagnosis wave submits A, which passes check_data.
            {'wave': 1.001, 'timed_trigger': False, 'root_nodes': ['B'], 'submitted_nodes': ['A']},
        ]
        check_data_results = [
            {'wave': 1.001, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 1},
            {'wave': 1.002, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0},
        ]
        # Create a networkx digraph of the relationship C -> B -> A
        node_graph.add_nodes_from(['A', 'B', 'C'])
        node_graph.add_edges_from([('C', 'B'), ('B', 'A')])

    elif index == 3:
        # Graph where A is the most base node, which has two branches split off from it
        # E -> D -> A
        # C -> B /
        sim_data = [
            # C and E have no incoming edges, and so are the root nodes.
            #   Both C and E timed out, and this leads to submitting all nodes.
            {'wave': 1.000, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
            # A and B have check_state=False, so they do not even run check_data. C is timed out and fails
            {'wave': 1.001, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
            # In the diagnose wave, B is submitted and fails check_data. This leads to submitting A. A passes check_data
            {'wave': 1.002, 'timed_trigger': False, 'root_nodes': ['B'], 'submitted_nodes': ['A']},
            # Then back to the regular wave. D has check_state=False, so it is not checked. E is submitted
            #   and fails its check_data (it had timed out). This triggers another diagnosis wave, whcih submits D.
            {'wave': 1.004, 'timed_trigger': False, 'root_nodes': ['E'], 'submitted_nodes': ['D']}
            # D check_data passes
        ]
        check_data_results = [
            {'wave': 1.001, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 1},
            {'wave': 1.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 1},
            {'wave': 1.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0},
            {'wave': 1.004, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 2},
            {'wave': 1.005, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0},
        ]

        node_graph.add_nodes_from(['A', 'B', 'C', 'D', 'E'])
        node_graph.add_edges_from([
            ('B', 'A'),
            ('C', 'B'),
            ('D', 'A'),
            ('E', 'D')
        ])

    elif index == 4:
        # Multiple timed triggered waves for a C -> B -> A graph
        sim_data = [
            {'wave': 1.000, 'timed_trigger': True, 'root_nodes': ['C'], 'submitted_nodes': ['A', 'B', 'C']},
            {'wave': 2.000, 'timed_trigger': True, 'root_nodes': ['C'], 'submitted_nodes': ['A', 'B', 'C']},
            {'wave': 2.001, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
            {'wave': 3.000, 'timed_trigger': True, 'root_nodes': ['C'], 'submitted_nodes': ['A', 'B', 'C']},
            {'wave': 3.001, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
            {'wave': 3.002, 'timed_trigger': False, 'root_nodes': ['B'], 'submitted_nodes': ['A']}
        ]

        check_data_results = [
            {'wave': 2.001, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 1},
            {'wave': 2.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0},
            {'wave': 3.001, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 2},
            {'wave': 3.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 1},
            {'wave': 3.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0},
        ]

        # Create a networkx digraph of the relationship C -> B -> A
        node_graph.add_nodes_from(['A', 'B', 'C'])
        node_graph.add_edges_from([('C', 'B'), ('B', 'A')])

    elif index == 5:
        # Multiple timed triggered waves for a C -> B -> A graph
        sim_data = [
            {'wave': 2.0, 'timed_trigger': True, 'root_nodes': ['C'], 'submitted_nodes': ['A', 'B']},
            {'wave': 3.0, 'timed_trigger': True, 'root_nodes': ['C'], 'submitted_nodes': ['A', 'B', 'C']},
            {'wave': 3.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']}
        ]

        check_data_results = [
            {'wave': 2.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.5819145692573678},
            {'wave': 3.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.7019422300331851},
            {'wave': 3.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.27469860848631633},
            {'wave': 3.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.3067809106558592}
        ]

        # Create a networkx digraph of the relationship C -> B -> A
        node_graph.add_nodes_from(['A', 'B', 'C'])
        node_graph.add_edges_from([('C', 'B'), ('B', 'A')])

    else:
        sim_data = []
        check_data_results = []

    return sim_data, check_data_results, node_graph


def fetch_large_sim_data():
    data = [
        {'wave': 3.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 3.002, 'timed_trigger': False, 'root_nodes': ['B'], 'submitted_nodes': ['A']},
        {'wave': 4.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 6.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 7.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 7.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 7.006, 'timed_trigger': False, 'root_nodes': ['E'], 'submitted_nodes': ['D']},
        {'wave': 8.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A']},
        {'wave': 8.001, 'timed_trigger': False, 'root_nodes': ['A'], 'submitted_nodes': []},
        {'wave': 10.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 11.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 13.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 13.002, 'timed_trigger': False, 'root_nodes': ['B'], 'submitted_nodes': ['A']},
        {'wave': 14.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 14.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 15.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 15.002, 'timed_trigger': False, 'root_nodes': ['D'], 'submitted_nodes': ['A']},
        {'wave': 17.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 19.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 20.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 21.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 21.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 21.006, 'timed_trigger': False, 'root_nodes': ['E'], 'submitted_nodes': ['D']},
        {'wave': 24.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 25.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 25.001, 'timed_trigger': False, 'root_nodes': ['A'], 'submitted_nodes': []},
        {'wave': 25.002, 'timed_trigger': False, 'root_nodes': ['D'], 'submitted_nodes': ['A']},
        {'wave': 27.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 27.002, 'timed_trigger': False, 'root_nodes': ['B'], 'submitted_nodes': ['A']},
        {'wave': 28.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 28.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 29.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 31.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 32.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A']},
        {'wave': 33.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 34.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 34.002, 'timed_trigger': False, 'root_nodes': ['B'], 'submitted_nodes': ['A']},
        {'wave': 35.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 35.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 35.006, 'timed_trigger': False, 'root_nodes': ['E'], 'submitted_nodes': ['D']},
        {'wave': 35.007, 'timed_trigger': False, 'root_nodes': ['D'], 'submitted_nodes': ['A']},
        {'wave': 38.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 39.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 40.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A']},
        {'wave': 40.001, 'timed_trigger': False, 'root_nodes': ['A'], 'submitted_nodes': []},
        {'wave': 41.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 42.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 42.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 42.006, 'timed_trigger': False, 'root_nodes': ['E'], 'submitted_nodes': ['D']},
        {'wave': 45.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 46.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 46.002, 'timed_trigger': False, 'root_nodes': ['D'], 'submitted_nodes': ['A']},
        {'wave': 48.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 49.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 49.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 49.006, 'timed_trigger': False, 'root_nodes': ['E'], 'submitted_nodes': ['D']},
        {'wave': 51.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A']},
        {'wave': 52.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 53.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 53.002, 'timed_trigger': False, 'root_nodes': ['D'], 'submitted_nodes': ['A']},
        {'wave': 55.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 55.002, 'timed_trigger': False, 'root_nodes': ['B'], 'submitted_nodes': ['A']},
        {'wave': 56.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 56.005, 'timed_trigger': False, 'root_nodes': ['E'], 'submitted_nodes': ['D']},
        {'wave': 58.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 58.002, 'timed_trigger': False, 'root_nodes': ['B'], 'submitted_nodes': ['A']},
        {'wave': 60.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 61.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 63.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 63.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 63.006, 'timed_trigger': False, 'root_nodes': ['E'], 'submitted_nodes': ['D']},
        {'wave': 66.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 67.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 68.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A']},
        {'wave': 69.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 70.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 70.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 71.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 73.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 73.002, 'timed_trigger': False, 'root_nodes': ['B'], 'submitted_nodes': ['A']},
        {'wave': 75.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 76.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 77.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 77.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 77.006, 'timed_trigger': False, 'root_nodes': ['E'], 'submitted_nodes': ['D']},
        {'wave': 77.007, 'timed_trigger': False, 'root_nodes': ['D'], 'submitted_nodes': ['A']},
        {'wave': 77.008, 'timed_trigger': False, 'root_nodes': ['A'], 'submitted_nodes': []},
        {'wave': 80.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 81.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 81.002, 'timed_trigger': False, 'root_nodes': ['D'], 'submitted_nodes': ['A']},
        {'wave': 81.003, 'timed_trigger': False, 'root_nodes': ['A'], 'submitted_nodes': []},
        {'wave': 83.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 84.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 84.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 84.006, 'timed_trigger': False, 'root_nodes': ['E'], 'submitted_nodes': ['D']},
        {'wave': 86.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A']},
        {'wave': 87.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 88.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 90.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 91.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 91.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 91.006, 'timed_trigger': False, 'root_nodes': ['E'], 'submitted_nodes': ['D']},
        {'wave': 94.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 95.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'D']},
        {'wave': 95.002, 'timed_trigger': False, 'root_nodes': ['D'], 'submitted_nodes': ['A']},
        {'wave': 97.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B']},
        {'wave': 98.0, 'timed_trigger': True, 'root_nodes': ['C', 'E'], 'submitted_nodes': ['A', 'B', 'C', 'D', 'E']},
        {'wave': 98.003, 'timed_trigger': False, 'root_nodes': ['C'], 'submitted_nodes': ['B']},
        {'wave': 98.006, 'timed_trigger': False, 'root_nodes': ['E'], 'submitted_nodes': ['D']},
        {'wave': 98.007, 'timed_trigger': False, 'root_nodes': ['D'], 'submitted_nodes': ['A']},
        {'wave': 98.008, 'timed_trigger': False, 'root_nodes': ['A'], 'submitted_nodes': []},
    ]

    error_data = [
        {'wave': 3.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.04839228919663863},
        {'wave': 3.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.165426654081397},
        {'wave': 4.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.5657165141872976},
        {'wave': 6.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.8313095875423099},
        {'wave': 7.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.1268224323251711},
        {'wave': 7.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.6129573170847538},
        {'wave': 7.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.03453687584100862},
        {'wave': 7.007, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.615238776631086},
        {'wave': 8.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.010482062042413642},
        {'wave': 10.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.9207604466261465},
        {'wave': 11.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.3411438051482649},
        {'wave': 13.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.9840066510947348},
        {'wave': 13.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.05353509389076849},
        {'wave': 13.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.9840066510947348},
        {'wave': 14.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.050654769536006894},
        {'wave': 14.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.8369549658494861},
        {'wave': 14.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.5203020774372277},
        {'wave': 15.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.07391539089000698},
        {'wave': 15.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.530689065949073},
        {'wave': 17.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.6246562358201785},
        {'wave': 19.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.9131160240231009},
        {'wave': 20.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.9014051480062379},
        {'wave': 20.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.42488875866653986},
        {'wave': 21.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.0990373887166548},
        {'wave': 21.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.1348712387758777},
        {'wave': 21.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.08560195080335353},
        {'wave': 21.007, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.7765227213153171},
        {'wave': 24.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.8512371315697511},
        {'wave': 25.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.028812072075891204},
        {'wave': 25.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.047400021399774395},
        {'wave': 25.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.028812072075891204},
        {'wave': 27.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.07894371123781863},
        {'wave': 27.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.46130259040526633},
        {'wave': 28.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.038756963000037836},
        {'wave': 28.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.7238342807407718},
        {'wave': 28.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.9478676466317988},
        {'wave': 29.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.9300073356654024},
        {'wave': 31.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.20834146386303187},
        {'wave': 32.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.7990835033593087},
        {'wave': 33.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.2704517109911494},
        {'wave': 34.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.053452388085988733},
        {'wave': 34.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.21721766356541783},
        {'wave': 35.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.06133310140101367},
        {'wave': 35.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.1714038189948277},
        {'wave': 35.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.18468163209140953},
        {'wave': 35.007, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.010995370944454352},
        {'wave': 35.008, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.7120621577223298},
        {'wave': 38.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.5260757060727482},
        {'wave': 39.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.454569183112405},
        {'wave': 40.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.025720409323914395},
        {'wave': 41.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.5424155217636647},
        {'wave': 42.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.005865579872314619},
        {'wave': 42.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.1761853510535778},
        {'wave': 42.005, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.4458242701854638},
        {'wave': 42.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.0932840875812635},
        {'wave': 42.007, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.4458242701854638},
        {'wave': 45.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.897891558851108},
        {'wave': 45.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.2880022188031369},
        {'wave': 46.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.017682501980609167},
        {'wave': 46.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.44513534278664124},
        {'wave': 48.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.9758100652218433},
        {'wave': 49.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.16514568525378592},
        {'wave': 49.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.85987996891139},
        {'wave': 49.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.029333338246737894},
        {'wave': 49.007, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.6942269758329117},
        {'wave': 51.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.48509696266770164},
        {'wave': 52.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.49067620352294417},
        {'wave': 53.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.06161486184253073},
        {'wave': 53.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.6419670551610351},
        {'wave': 55.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.07834063634306898},
        {'wave': 55.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.47336833028548186},
        {'wave': 56.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.3579915234626303},
        {'wave': 56.005, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.10784332524115747},
        {'wave': 56.006, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.4825866367948497},
        {'wave': 58.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.0914694284079326},
        {'wave': 58.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.8695661790887571},
        {'wave': 60.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.827666541562193},
        {'wave': 61.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.34260535477756504},
        {'wave': 63.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.5826965899615474},
        {'wave': 63.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.15709307237138492},
        {'wave': 63.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.37446576190617886},
        {'wave': 63.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.16704190009183917},
        {'wave': 63.007, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.1733872392949536},
        {'wave': 66.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.7391235639824538},
        {'wave': 67.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.10659852473007658},
        {'wave': 68.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.09943254283742775},
        {'wave': 69.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.598587355583124},
        {'wave': 70.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.08681180392939736},
        {'wave': 70.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.3236711274306401},
        {'wave': 70.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.2670046129536824},
        {'wave': 71.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.949148783272111},
        {'wave': 73.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.7876297433706368},
        {'wave': 73.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.04551989453122107},
        {'wave': 73.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.7876297433706368},
        {'wave': 75.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.8477959149548795},
        {'wave': 76.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.7896244835270244},
        {'wave': 77.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.0862283495953633},
        {'wave': 77.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.9548177274349144},
        {'wave': 77.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.010697548831159476},
        {'wave': 77.007, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.08384609784495389},
        {'wave': 77.008, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.04506027412199198},
        {'wave': 80.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.16301541452738677},
        {'wave': 81.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.08609768898995918},
        {'wave': 81.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.01339429915509871},
        {'wave': 83.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.2345195386349056},
        {'wave': 84.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.16935086263624377},
        {'wave': 84.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.20352177119019677},
        {'wave': 84.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.16259713492097339},
        {'wave': 84.007, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.2977417879041043},
        {'wave': 86.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.862626219764329},
        {'wave': 87.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.8262634362251375},
        {'wave': 88.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.6113063826253506},
        {'wave': 90.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.91452772328466},
        {'wave': 91.001, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.6762874650193177},
        {'wave': 91.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.043071479292588366},
        {'wave': 91.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.916409154510307},
        {'wave': 91.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.08122998084831157},
        {'wave': 91.007, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.518981739343548},
        {'wave': 94.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.25063471133041815},
        {'wave': 95.002, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.03404779209200448},
        {'wave': 95.003, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.24205307925765174},
        {'wave': 97.002, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.29701571139603755},
        {'wave': 98.003, 'node': 'C', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.10500153806199664},
        {'wave': 98.004, 'node': 'B', 'check_type': 'check_data', 'failure_magnitude': 0, 'data': 0.37760407760723635},
        {'wave': 98.006, 'node': 'E', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.09205220341353204},
        {'wave': 98.007, 'node': 'D', 'check_type': 'check_data', 'failure_magnitude': 2, 'data': 0.044213821999009806},
        {'wave': 98.008, 'node': 'A', 'check_type': 'check_data', 'failure_magnitude': 1, 'data': 0.0004238213444038852},
    ]

    import networkx as nx
    graph = nx.DiGraph()
    graph.add_nodes_from(['A', 'B', 'C', 'D', 'E'])
    graph.add_edges_from([('C', 'B'), ('B', 'A'), ('E', 'D'), ('D', 'A')])

    return data, error_data, graph