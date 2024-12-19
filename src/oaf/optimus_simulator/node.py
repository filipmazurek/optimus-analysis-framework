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
