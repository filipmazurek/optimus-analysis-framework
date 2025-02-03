import random
import numpy as np
from abc import ABC


class Node(ABC):
    """
    Base class for an Optimus node. Must have at least a name and a timeout value.
    """

    def __init__(self, **kwargs):
        assert 'name' in kwargs
        assert 'timeout' in kwargs

        self.name = kwargs['name']
        self.timeout = kwargs['timeout']
        self.failed = False
        self.last_calibration = 0.
        self.last_check = 0.
        self.failure_magnitude = 0  # 0: No failure, 1: Minor failure, 2: Major failure
        self.check_data = None

    def simulate_failure(self):
        """Simulate failure for the node. Typically done at every timestep of the sim."""
        pass

    def get_check_data(self):
        """Get the most recent check data for the node"""
        return {
            'data': self.check_data,
            'failure_magnitude': self.failure_magnitude
        }

    def get_all_data(self):
        """Reserved function to get all data from the node"""
        pass

    def calibrate(self, time):
        """Calibrate the node"""
        self.failed = False
        self.last_calibration = time
        self.failure_magnitude = 0


class SimpleNode(Node):
    """
    Simple node that fails with a given probability at every time step.
    For the simplest simulations
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        assert 'failure_prob' in kwargs
        self.failure_prob = kwargs['failure_prob']

    def simulate_failure(self):
        if self.failed:
            return

        self.check_data = random.random()
        self.failed = self.check_data < self.failure_prob
        # Create a random integer (0 to 2) to simulate the magnitude of the failure
        if self.failed:
            self.failure_magnitude = random.randint(1, 2)


class DistributionThresholdNode(Node):
    """
    Node that at every step of the simulation will generate `num_samples` data points from a distribution
    and check if the samples satisfy some property
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        assert 'dist_type' in kwargs, "'dist_type' is required for DistributionMeanThresholdNode."
        assert 'dist_mean' in kwargs, "'dist_mean' is required for DistributionMeanNode."
        assert 'dist_std' in kwargs, "'dist_std' is required for DistributionMeanNode."
        assert 'num_samples' in kwargs, "'num_samples' is required for DistributionMeanNode."
        assert 'threshold' in kwargs, "'threshold' is required for DistributionMeanNode."
        assert 'comparison_func' in kwargs, "'comparison_func' is required for DistributionMeanNode."

        dist_type = kwargs['dist_type']
        self.dist_mean = kwargs['dist_mean']
        self.dist_std = kwargs['dist_std']
        self.num_samples = kwargs['num_samples']
        self.threshold = kwargs['threshold']
        self.comparison_func = kwargs['comparison_func']
        self.check_data = []
        self.metadata = {'dist_mean': self.dist_mean, 'dist_std': self.dist_std, 'num_samples': self.num_samples}
        # Select the distribution function
        if dist_type == 'normal':
            self.dist_func = np.random.normal
        elif dist_type == 'uniform':
            self.dist_func = np.random.uniform
        elif dist_type == 'poisson':
            self.dist_func = np.random.poisson
        elif dist_type == 'exponential':
            self.dist_func = np.random.exponential
        elif dist_type == 'gamma':
            self.dist_func = np.random.gamma
        else:
            raise ValueError(f"Invalid distribution type: {dist_type}")

    def simulate_failure(self):
        if self.failed:
            return

        # Generate random data
        self.check_data = self.dist_func(self.dist_mean, self.dist_std, self.num_samples)

        # Use the comparison function to determine if the node failed
        self.failed = self.comparison_func(list(self.check_data), self.threshold)

        # Check failure magnitude
        if self.failed:
            self.failure_magnitude = 1


class TrendNode(Node):
    """
    Node that simulates a trend with drift and noise. Fails when the trend crosses a threshold.
    Similar in idea to drifting parameters in a device.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        assert 'initial_value' in kwargs, "'initial_value' is required for TrendNode."
        assert 'drift_rate' in kwargs, "'drift_rate' is required for TrendNode."
        assert 'noise_std' in kwargs, "'noise_std' is required for TrendNode."
        assert 'threshold' in kwargs, "'threshold' is required for TrendNode."

        self.check_data = kwargs['initial_value']
        self.drift_rate = kwargs['drift_rate']
        self.noise_std = kwargs['noise_std']
        self.threshold = kwargs['threshold']

    def simulate_failure(self):
        if self.failed:
            return

        # Simulate drift and noise
        drift = self.drift_rate
        noise = np.random.normal(0, self.noise_std)
        self.check_data += drift + noise

        # Determine failure
        self.failed = self.check_data > self.threshold

        # Simulate failure magnitude
        if self.failed:
            self.failure_magnitude = 1 + int(abs(self.check_data - self.threshold) > self.noise_std)


class ExpDecayFuncNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Default values
        defaults = {
            'amp': 1.0,
            'decay_time': 10.0,  # time in µs
            'background': 0.0,
            'threshold': 0.992,  # Acceptable population threshold. Desire 99.9%
            # Drift rate in absolute units. Will be multiplied by a random number between -1 and 1
            'amp_drift_rate': 0.01,
            # Bias positive drift. 0.5 is no bias, 0 is always negative, 1 is always positive
            'amp_drift_bias': 0.5,
            'decay_time_drift_rate': 0.1,
            'decay_time_drift_bias': 0.5,
            'background_drift_rate': 0.001,
            'background_drift_bias': 0.5
        }

        # Override defaults with kwargs if provided
        for key, default in defaults.items():
            setattr(self, key, kwargs.get(key, default))

        self.parameters = [
            'amp',
            'decay_time',
            'background',
        ]
        self.initial_params = {
            'amp': self.amp,
            'decay_time': self.decay_time,
            'background': self.background,
        }
        self.current_params = self.initial_params.copy()
        self.threshold = self.threshold
        self.drift_rates = {
            'amp': self.amp_drift_rate,
            'decay_time': self.decay_time_drift_rate,
            'background': self.background_drift_rate,
        }
        self.drift_biases = {
            'amp': self.amp_drift_bias,
            'decay_time': self.decay_time_drift_bias,
            'background': self.background_drift_bias,
        }
        self.parameter_min_values = {
            'amp': 0.1,
            'decay_time': 0.1,
            'background': 0.0,
        }

        # Used to store the parameters right before calibration, therefore saving the out-of-spec parameters
        self.params_at_calibration = []

    def exp_decay(self, time):
        amp = self.current_params['amp']
        decay_time = self.current_params['decay_time']
        background = self.current_params['background']
        return amp * np.exp(-time / decay_time) + background

    def drift_parameters(self):
        for param in self.parameters:
            # Decide drift direction
            if np.random.uniform() < self.drift_biases[param]:
                direction = 1
            else:
                direction = -1
            drift = direction * self.drift_rates[param] * np.random.uniform()
            self.current_params[param] = max(self.parameter_min_values[param], self.current_params[param] + drift)

    def _check_value(self):
        """
        Check data at the 99.9% decay point
        """
        time_point = -self.current_params['decay_time'] * np.log(1 - .999)
        value = self.exp_decay(time_point)

        return value

    def run_check(self):
        """
        Perform the check at the 99.9% decay point and evaluate results.
        """
        value = self._check_value()
        result = (1 - value) > self.threshold

        return result

    def calibrate(self, time):
        super().calibrate(time)

        # Save the parameters right before calibration
        current_params = self.current_params.copy()
        current_params['wave'] = time
        self.params_at_calibration.append(current_params)

        # Reset to initial parameters
        self.current_params = self.initial_params.copy()

    def _check_failure_magnitude(self):
        """
        Check failure magnitude based on how close the value is to the threshold.
        """
        value = self._check_value()
        if self.threshold - (1 - value) < 0.:
            return 0
        if self.threshold - (1 - value) < 0.01:
            return 1
        else:
            return 2

    def simulate_failure(self):
        # Used every step of the simulation, therefore must include drift
        # Simulate drift
        self.drift_parameters()

        # A node can drift out of and back into spec. Allow it to do so.
        self.check_data = self._check_value()
        result = self.run_check()
        self.failed = not result
        self.failure_magnitude = self._check_failure_magnitude()

    def get_all_data(self):
        super().get_all_data()

        return self.params_at_calibration