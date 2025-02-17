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
        self.base_timeout = kwargs['timeout']
        self.timeout = kwargs['timeout']
        self.failed = False
        self.last_calibration = 0.
        self.last_check = 0.
        self.failure_magnitude = 0  # 0: No failure, 1: Minor failure, 2: Major failure
        self.check_data_value = None

        # Flags for timeout-aware adaptive Optimus
        self.first_check_delayed_flag = False
        self.long_lived_flag = False

        if 'delay_first_check' in kwargs:
            assert isinstance(kwargs['delay_first_check'], bool)
            self.delay_first_check = kwargs['delay_first_check']
        else:
            self.delay_first_check = False

        if self.delay_first_check:
            assert 'fifth_percentile_ttf' in kwargs
            self.fifth_percentile_ttf = kwargs['fifth_percentile_ttf']

        if 'check_long_lived_nodes' in kwargs:
            assert isinstance(kwargs['check_long_lived_nodes'], bool)
            self.check_long_lived_nodes = kwargs['check_long_lived_nodes']
        else:
            self.check_long_lived_nodes = False

        if self.check_long_lived_nodes:
            assert 'ninety_fifth_percentile_ttf' in kwargs
            self.ninety_fifth_percentile_ttf = kwargs['ninety_fifth_percentile_ttf']

        if 'fifth_percentile_ttf' in kwargs and 'ninety_fifth_percentile_ttf' in kwargs:
            assert self.ninety_fifth_percentile_ttf > self.fifth_percentile_ttf > 0.

    def modify_timeout(self, new_timeout):
        self.timeout = new_timeout

    def reset_to_initial_timeout(self):
        self.timeout = self.base_timeout

    def simulate_failure(self):
        """Simulate failure for the node. Typically done at every timestep of the sim."""
        pass

    def get_check_data(self):
        """Get the most recent check data for the node"""
        return {
            'data': self.check_data_value,
            'failure_magnitude': self.failure_magnitude
        }

    def get_all_data(self):
        """Reserved function to get all data from the node"""
        pass

    def check_data(self, time):
        failed = self.failed

        # If the timeout was increased and this is the first check since then, reset the timeout
        if self.first_check_delayed_flag:
            self.first_check_delayed_flag = False
            self.timeout = self.base_timeout

        # If the node is long-lived, check if the 95th percentile ttf is greater than the current wait time value
        if self.check_long_lived_nodes and not self.long_lived_flag:
            time_alive = max(self.last_calibration, self.last_check) - time
            if time_alive > self.ninety_fifth_percentile_ttf:
                # TODO: set values that make sense
                self.modify_timeout(self.tiemout / 2)
                self.long_lived_flag = True

        return failed

    def calibrate(self, time):
        """Calibrate the node"""
        self.failed = False
        self.last_calibration = time
        self.failure_magnitude = 0

        self.long_lived_flag = False

        # Perform adaptive Optimus timeout adjustment
        if self.delay_first_check:
            # If the 5th percentile ttf is much greater than the current timeout, increase the timeout
            # TODO: set values that make sense
            if self.fifth_percentile_ttf > 3 * self.timeout:
                self.modify_timeout(self.fifth_percentile_ttf / 3)
                self.first_check_delayed_flag = True

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

        self.check_data_value = random.random()
        self.failed = self.check_data_value < self.failure_prob
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
        self.check_data_value = []
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
        self.check_data_value = self.dist_func(self.dist_mean, self.dist_std, self.num_samples)

        # Use the comparison function to determine if the node failed
        self.failed = self.comparison_func(list(self.check_data_value), self.threshold)

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

        self.check_data_value = kwargs['initial_value']
        self.drift_rate = kwargs['drift_rate']
        self.noise_std = kwargs['noise_std']
        self.threshold = kwargs['threshold']

    def simulate_failure(self):
        if self.failed:
            return

        # Simulate drift and noise
        drift = self.drift_rate
        noise = np.random.normal(0, self.noise_std)
        self.check_data_value += drift + noise

        # Determine failure
        self.failed = self.check_data_value > self.threshold

        # Simulate failure magnitude
        if self.failed:
            self.failure_magnitude = 1 + int(abs(self.check_data_value - self.threshold) > self.noise_std)


class FuncNode(Node, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parameter_setup(**kwargs)
        # Used to store the parameters right before calibration, therefore saving the out-of-spec parameters
        self.params_at_calibration = []

    def parameter_setup(self, **kwargs):
        # Must set up the following:
        #   self.parameters: list of strings
        #   self.initial_params: dict of initial parameter values
        #   self.current_params: dict of current parameter values
        #   self.threshold: float
        #   self.drift_rates: dict of drift rates
        #   self.drift_biases: dict of drift biases
        #   self.parameter_min_values: dict of minimum parameter values
        #   self.parameter_max_values: dict of maximum parameter values
        pass

    def drift_parameters(self):
        for param in self.parameters:
            # Decide drift direction
            if np.random.uniform() < self.drift_biases[param]:
                direction = 1
            else:
                direction = -1
            drift = direction * self.drift_rates[param] * np.random.uniform()
            # Ensure that the new parameter is between the max and min values
            new_param = self.current_params[param] + drift
            new_param = max(self.parameter_min_values[param], new_param)
            self.current_params[param] = min(self.parameter_max_values[param], new_param)

    def _check_value(self):
        """
        Check data at the desired point
        """
        pass

    def run_check(self):
        """
        Perform the check at the 99.9% decay point and evaluate results.
        """
        value = self._check_value()
        return value > self.threshold

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
        if abs(self.threshold - value) < 0.:
            return 0
        if abs(self.threshold - value) < 0.01:
            return 1
        else:
            return 2

    def simulate_failure(self):
        # Used every step of the simulation, therefore must include drift
        # Simulate drift
        self.drift_parameters()

        # A node can drift out of and back into spec. Allow it to do so.
        self.check_data_value = self._check_value()
        result = self.run_check()
        self.failed = not result
        self.failure_magnitude = self._check_failure_magnitude()

    def get_all_data(self):
        super().get_all_data()

        return self.params_at_calibration


class Sin2FuncNode(FuncNode):

    def parameter_setup(self, **kwargs):
        # Default values
        defaults = {
            'omega': 1.0,
            'time': 1.0,  # arbitrary time unit
            'delta': 0.0,  # delta for cos2 error term
            'background': 0.0,  # experimental error. Should be < 0
            'threshold': 0.992,  # Acceptable population threshold
            # Drift rate in absolute units. Will be multiplied by a random number between -1 and 1
            'omega_drift_rate': 0.01,
            # Bias positive drift. 0.5 is no bias, 0 is always negative, 1 is always positive
            'omega_drift_bias': 0.5,
            'time_drift_rate': 0.1,
            'time_drift_bias': 0.5,
            'background_drift_rate': 0.001,
            'background_drift_bias': 0.5
        }

        # Override defaults with kwargs if provided
        for key, default in defaults.items():
            setattr(self, key, kwargs.get(key, default))

        self.parameters = [
            'omega',
            'time',
            'delta',
            'background'
        ]
        self.initial_params = {
            'omega': self.omega,
            'time': self.time,
            'delta': self.delta,
            'background': self.background
        }
        self.current_params = self.initial_params.copy()
        self.threshold = self.threshold
        self.drift_rates = {
            'omega': self.omega_drift_rate,
            'time': self.time_drift_rate,
            'delta': self.delta_drift_rate,
            'background': self.background_drift_rate,
        }
        self.drift_biases = {
            'omega': self.omega_drift_bias,
            'time': self.time_drift_bias,
            'delta': self.delta_drift_bias,
            'background': self.background_drift_bias,
        }
        self.parameter_min_values = {
            'omega': 0.1,
            'time': 0.1,
            'delta': -100.,
            'background': -100.,
        }

        self.parameter_max_values = {
            'omega': 100.,
            'time': 100.,
            'delta': 100.,
            'background': 0.,
        }

    def sin2_with_error(self, time):
        omega = self.current_params['omega']
        time = self.current_params['time']
        delta = self.current_params['delta']
        background = self.current_params['background']
        return np.sin(omega * np.pi * time) ** 2 * np.cos(delta) ** 2 + background

    def _check_value(self):
        """
        Check data at the desired point
        """
        return self.sin2_with_error()


class ExpDecayFuncNode(Node):

    def parameter_setup(self, **kwargs):

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
            'background_drift_bias': 0.5,
            'time_drift_rate': 0.,
            'time_drift_bias': 0.5
        }

        # Override defaults with kwargs if provided
        for key, default in defaults.items():
            setattr(self, key, kwargs.get(key, default))

        # Calculate the time parameter based on the decay time. Drifts in time here model drifts in the control
        self.time = -self.decay_time * np.log(1 - .999)

        self.parameters = [
            'amp',
            'time',
            'decay_time',
            'background',
        ]
        self.initial_params = {
            'amp': self.amp,
            'time': self.time,
            'decay_time': self.decay_time,
            'background': self.background,
        }
        self.current_params = self.initial_params.copy()
        self.threshold = self.threshold
        self.drift_rates = {
            'amp': self.amp_drift_rate,
            'time': self.time_drift_rate,
            'decay_time': self.decay_time_drift_rate,
            'background': self.background_drift_rate,
        }
        self.drift_biases = {
            'amp': self.amp_drift_bias,
            'time': self.time_drift_bias,
            'decay_time': self.decay_time_drift_bias,
            'background': self.background_drift_bias,
        }
        self.parameter_min_values = {
            'amp': 0.1,
            'time': 0.0001,
            'decay_time': 0.1,
            'background': -100.,
        }

        self.parameter_max_values = {
            'amp': 100.,
            'time': 100.,
            'decay_time': 100.,
            'background': 100.,
        }

        # Used to store the parameters right before calibration, therefore saving the out-of-spec parameters
        self.params_at_calibration = []

    def exp_decay(self):
        amp = self.current_params['amp']
        time = self.current_params['time']
        decay_time = self.current_params['decay_time']
        background = self.current_params['background']
        return amp * np.exp(-time / decay_time) + background

    def _check_value(self):
        """
        Check data at the 99.9% decay point
        """
        return 1 - self.exp_decay()
