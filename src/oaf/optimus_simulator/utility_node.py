import numpy as np
from oaf.optimus_simulator.node import FuncNode, ExpDecayFuncNode
from oaf.optimus_simulator.hidden_node import CompensatingExpDecayNode


class RandomlyChangeParamNode(FuncNode):
    """Node that may drift its parameter value by a large amount at calibration. Simulates something that causes the
    parameter to change by a large amount and exposes it to dependent nodes.
    Used for the paper experiment to simulate a node whose parameter sometimes changes and leads to error in the node
    that depends on this one.
    """
    def __init__(self, **kwargs):
        # Must have a dependent node to source own correctness
        assert 'dependent_nodes' in kwargs
        assert 'dependence' in kwargs['dependent_nodes']
        super().__init__(**kwargs)

    def parameter_setup(self, **kwargs):
        # Default values
        defaults = {
            'param': 0.,
            'param_drift_rate': 0,
            'param_drift_bias': 0.8,
            'param_calibration_drift_amount': 1.,
            'check_data_failure_rate': 0.1,
        }

        # Override defaults with kwargs if provided
        for key, default in defaults.items():
            setattr(self, key, kwargs.get(key, default))

        self.parameters = [
            'param',
        ]
        self.initial_params = {
            'param': self.param,
        }

        self.current_params = self.initial_params.copy()

        self.drift_rates = {
            'param': self.param_drift_rate,
        }
        self.drift_biases = {
            'param': self.param_drift_bias,
        }
        self.parameter_min_values = {
            'param': -np.inf,
        }
        self.parameter_max_values = {
            'param': np.inf,
        }

    def run_check(self):
        return self.dependent_nodes['dependence'].run_check()

    def check_data(self, time):
        # Check if the dependent node has failed (which must be set with an infinite timeout)
        #   This is just used as a technicality so that the failure method can be flexible for this node
        return self.dependent_nodes['dependence'].check_data(time)

    def calibrate(self, time):
        # Save the parameters right before calibration
        self.params_before_calibration = self.current_params.copy()

        # With some probability, change the parameter value by a large amount
        if np.random.rand() < self.check_data_failure_rate:
            # Change the parameter value by a large amount
            self.current_params['param'] += self.param_calibration_drift_amount

        self.params_after_calibration = self.current_params.copy()

        # Perform basic maintenance
        self.failed = False
        self.last_calibration = time
        self.failure_magnitude = 0


    def get_param(self):
        return self.current_params['param']


class RandomlyChangeParamNodeCombinedWithTargetNode(FuncNode):
    """A RandomlyChangeParamNode that is combined with a target node into a single node. This simulates combining two
    nodes after dependency analysis.
    """

    def __init__(self, **kwargs):
        # Must have a dependent node to source own correctness
        assert 'dependent_nodes' in kwargs
        assert 'dependence' in kwargs['dependent_nodes']

        self.target_node = CompensatingExpDecayNode(name='B', timeout=np.inf, dependent_nodes={'dependence': self},
                                                    amp_drift_rate=0., background_drift_rate=0., time_drift_rate=0.)

        super().__init__(**kwargs)

    def parameter_setup(self, **kwargs):
        # Default values
        defaults = {
            'param': 0.,
            'param_drift_rate': 0,
            'param_drift_bias': 0.8,
            'param_calibration_drift_amount': 1.,
            'check_data_failure_rate': 0.1,
        }

        # Override defaults with kwargs if provided
        for key, default in defaults.items():
            setattr(self, key, kwargs.get(key, default))

        self.parameters = [
            'param',
        ]
        self.initial_params = {
            'param': self.param,
        }

        self.current_params = self.initial_params.copy()

        self.drift_rates = {
            'param': self.param_drift_rate,
        }
        self.drift_biases = {
            'param': self.param_drift_bias,
        }
        self.parameter_min_values = {
            'param': -np.inf,
        }
        self.parameter_max_values = {
            'param': np.inf,
        }

    def run_check(self):
        own_correctness = self.dependent_nodes['dependence'].run_check()
        target_correctness = self.target_node.run_check()
        return own_correctness and target_correctness

    def check_data(self, time):
        # Check if the dependent node has failed (which must be set with an infinite timeout)
        #   This is just used as a technicality so that the failure method can be flexible for this node
        own_check_data = self.dependent_nodes['dependence'].check_data(time)
        target_check_data = self.target_node.check_data(time)
        return own_check_data and target_check_data

    def calibrate(self, time):
        # Save the parameters right before calibration
        self.params_before_calibration = self.current_params.copy()

        # With some probability, change the parameter value by a large amount
        if np.random.rand() < self.check_data_failure_rate:
            # Change the parameter value by a large amount
            self.current_params['param'] += self.param_calibration_drift_amount

        # Calibrate the combined target node
        self.target_node.calibrate(time)

        self.params_after_calibration = self.current_params.copy()

        # Perform basic maintenance
        self.failed = False
        self.last_calibration = time
        self.failure_magnitude = 0


    def get_param(self):
        return self.current_params['param']