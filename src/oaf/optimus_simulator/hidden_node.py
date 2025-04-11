import numpy as np
from oaf.optimus_simulator.node import Node, FuncNode, ExpDecayFuncNode


class HiddenNode(FuncNode):
    """Node which cannot be calibrated or checked. Used to represent events which are not directly part of calibration,
    such as temporary voltage noise or ambient temperature fluctuations.
    """

    def simulate_failure(self, time=None):
        # Override the simulate_failure method to only drift parameters
        # Used every step of the simulation, simulate drift
        self.drift_parameters()

    def check_data(self, _):
        # Hidden nodes are never failures
        return False


class OneParamHiddenNode(HiddenNode):
    """Node whose parameter approximitely increases linearly with time."""

    def parameter_setup(self, **kwargs):
        # Default values
        defaults = {
            'param': 0.,
            # Drift rate in absolute units. Will be multiplied by a random number between -1 and 1
            'param_drift_rate': 1e-3,
            # Bias positive drift. 0.5 is no bias, 0 is always negative, 1 is always positive
            'param_drift_bias': 0.8,
        }

        # Override defaults with kwargs if provided
        for key, default in defaults.items():
            setattr(self, key, kwargs.get(key, default))

        self.parameters = [
            'param',
        ]
        self.current_params = {
            'param': self.param,
        }
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

    def get_param(self):
        return np.floor(self.current_params['param'])


class CompensatingExpDecayNode(ExpDecayFuncNode):
    """Node which calibrates based on some dependent value. Uses the hidden dependent value as a baseline"""

    def __init__(self, **kwargs):
        # Compensation value for the hidden param
        self.compensation = 0.

        # Must have a dependent node to source the background value
        assert 'dependent_nodes' in kwargs
        assert 'dependence' in kwargs['dependent_nodes']
        # dependent_nodes must be of the type HiddenNode
        assert hasattr(kwargs['dependent_nodes']['dependence'], 'get_param')
        super().__init__(**kwargs)


    def exp_decay(self):
        val = super().exp_decay()
        # Compensate for the hidden node value
        val += self.dependent_nodes['dependence'].get_param() - self.compensation
        return val

    def calibrate(self, time):
        # Calibrate as usual
        super().calibrate(time)
        # Compensate for the hidden node value
        self.compensation =  self.dependent_nodes['dependence'].get_param()
