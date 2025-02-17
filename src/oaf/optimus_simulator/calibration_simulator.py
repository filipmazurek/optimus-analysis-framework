from oaf.optimus_simulator.node import Node

# TODO: Timeout is currently not used. Implement timeout functionality
class QuantumCalibrationSimulator:
    """
    A simple simulator for the Optimus algorithm. This simulator holds a number of nodes, each of which can fail
    at every time step according to the node failure function. The simulator simulates node failures and runs the
    Optimus algorithm to diagnose and recalibrate the nodes. The output of the simulation is the same as from
    a real quantum device.
    """
    def __init__(self, graph, nodes, root_nodes, time_step=1, timeout=10):
        """
        Initialize the simulator.

        :param graph: NetworkX DiGraph representing the node relationships.
        :param nodes: Dict of Nodes used to simulate calibration. Of the form {node_name: Node}.
        :param root_nodes: The root nodes for recursive DFS.
        :param time_step: The simulation step size.
        :param timeout: Number of time units before triggering timeout for nodes.
        """
        assert isinstance(time_step, int) and time_step > 0
        assert isinstance(timeout, int) and timeout > 0
        assert set(graph.nodes) == set(nodes.keys())
        for n in nodes.keys():
            assert n in graph.nodes
        for n in nodes.values():
            assert isinstance(n, Node)
        self.graph = graph
        self.root_nodes = root_nodes
        self.time_step = time_step
        self.timeout = timeout
        self.wave_data = []  # Stores the simulation data (waves, root_nodes, submitted_nodes)
        self.check_data_results = []
        self.nodes = nodes
        self.wave_offset = 0  # Global offset to avoid workarounds for diagnosis wave separation
        self.current_time = 0.
        self.ground_truth = []

    def simulate(self, total_time_steps):
        """Run the simulation for a number of time steps."""
        while self.current_time < total_time_steps:

            # Step 0: Check all node correctness values and record. Simulation base truth
            current_ground_truth = {'time': self.current_time}
            for node_name, node in self.nodes.items():
                current_ground_truth[node_name] = not node.failed
            self.ground_truth.append(current_ground_truth)

            # Step 1: Check for timed out nodes
            timed_out_nodes = [
                node_name for node_name, node in self.nodes.items()
                if self.current_time - node.last_check >= node.timeout
            ]

            # Step 2: Handle timed out nodes
            submitted_nodes = []
            if timed_out_nodes:
                wave_data, submitted_nodes = self._submit_timed_trigger(timed_out_nodes)
                self.wave_data += wave_data

            # Step 3: Handle wave algorithm submitted nodes
            self.wave_offset = 0  # Reset the wave offset
            for node in submitted_nodes:
                wave_data, check_data_results = self._check_node(node)
                self.wave_data += wave_data
                self.check_data_results += check_data_results

            # Step 4: Advance the simulation
            self._simulate_failures()
            self.current_time += self.time_step

    def _get_all_dependencies(self, node_name):
        dependency_nodes = []

        def recurse(node):
            for successor in self.graph.successors(node):
                if successor not in dependency_nodes:
                    recurse(successor)
                    dependency_nodes.append(successor)

        recurse(node_name)

        return dependency_nodes

    def _check_failure(self, node):
        """Check if any of the node's dependencies have failed. If so, the node is marked as failed as well."""
        # Perform `check_data` on the node
        failed = node.check_data(self.current_time)
        # Check if the node has already failed
        if failed:
            return True
        # Check if any of the node's dependencies have failed
        dependencies = self._get_all_dependencies(node.name)
        return any(self.nodes[dep].failed for dep in dependencies)

    def _submit_timed_trigger(self, timed_out_nodes):
        """Handles submission of nodes that timed out."""
        submitted_nodes = []

        for node in timed_out_nodes:
            # Find all dependencies of the timed out nodes
            dependency_nodes = self._get_all_dependencies(node)
            # Add nodes in DFS order
            submitted_nodes += dependency_nodes
            submitted_nodes += node
            # Trick to remove possible duplicates
            submitted_nodes = list(dict.fromkeys(submitted_nodes))

        # Update last submission time
        for node in submitted_nodes:
            self.nodes[node].last_submission = self.current_time

        # Record this wave
        wave_data = [{
            'wave': self.current_time,
            'timed_trigger': True,
            'root_nodes': self.root_nodes,
            'submitted_nodes': submitted_nodes,
        }]

        return wave_data, submitted_nodes

    def _check_state(self, node_name):
        """Check the state of a node."""
        node = self.nodes[node_name]

        # 1. Timeout check
        max_check_time = max(node.last_calibration, node.last_check)
        if self.current_time - max_check_time >= node.timeout:
            return False

        # 2. Dependent calibration check. If any of the node's dependencies have been re-calibrated
        #   since the last check, then the node must be re-calibrated.
        for successor in self.graph.successors(node_name):
            if self.nodes[successor].last_calibration > max_check_time:
                return False

        # Assume the node is in spec
        return True

    def _check_node(self, check_node, diagnosis=False):
        """Handles submission of nodes """
        # Running the wave algorithm on a node increments the wave offset
        self.wave_offset += 1
        # Save current iteration's wave offset to account for recursion
        check_offest = self.wave_offset

        wave_data = []
        check_data_results = []
        node = self.nodes[check_node]

        # Check state only runs if not performing diagnosis wave
        if not diagnosis:
            check_state_result = self._check_state(check_node)

        # check_state if the node is assumed to be in spec
        if not diagnosis and check_state_result:  # If not diagnosis, will have a check_state_result val
            return wave_data, check_data_results

        # check_data. Result of check_data is stored in node.failed as a proxy
        node.last_check = self.current_time
        # Get all the check_data information from the node
        node_check_data = node.get_check_data()

        if not self._check_failure(node):
            check_data_results += [{
                'wave': self.current_time + check_offest * 0.001,
                'node': check_node,
                'check_type': 'check_data',
                'failure_magnitude': 0,
                **node_check_data
            }]
            return wave_data, check_data_results

        # If the node failed, start a diagnosis wave
        successors = list(self.graph.successors(check_node))
        for successor in successors:
            result = self._check_node(successor, diagnosis=True)
            wave_data += result[0]
            check_data_results += result[1]

        # Save failure magnitude for use in the failure data
        failure_magnitude = node.failure_magnitude

        # Recalibrate this node
        node.calibrate(self.current_time)

        # Wave data from this node
        wave_data += [{
            'wave': self.current_time + check_offest * 0.001,
            'timed_trigger': False,
            'root_nodes': list(check_node),
            'submitted_nodes': successors,
        }]
        # Failure data from this node
        check_data_results += [{
            'wave': self.current_time + check_offest * 0.001,
            'node': check_node,
            'check_type': 'check_data',
            'failure_magnitude': failure_magnitude,
            **node_check_data
        }]
        
        return wave_data, check_data_results

    def _simulate_failures(self):
        """Simulate failures for each node based on their failure probability."""
        # Simulate failure for each time step
        for step in range(self.time_step):
            for _, node in self.nodes.items():
                node.simulate_failure()

    def get_wave_data(self):
        """Get the wave data."""
        return self.wave_data
    
    def get_check_data_results(self):
        """Get the failure data."""
        return self.check_data_results

    def get_ground_truth(self):
        """Get the ground truth data."""
        return self.ground_truth
