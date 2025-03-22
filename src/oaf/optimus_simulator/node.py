import ms_gate
import random
import numpy as np
import qutip as qt
from abc import ABC
from scipy.stats import gamma


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
        self.num_first_checks_to_delay = 2
        self.cur_num_first_checks_delayed = 0

        # Flags for timeout-aware adaptive Optimus
        self.first_check_delayed_flag = False
        self.long_lived_flag = False

        # For connecting to dependent nodes
        if 'dependent_nodes' in kwargs:
            self.dependent_nodes = kwargs['dependent_nodes']
        else:
            self.dependent_nodes = {}

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

    def reset_to_initial_timeout(self):
        self.timeout = self.base_timeout

    def simulate_failure(self, time=None):
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
                self.timeout = self.base_timeout / 2
                self.long_lived_flag = True

        return failed

    def calibrate(self, time):
        """Calibrate the node"""
        self.failed = False
        self.last_calibration = time
        self.failure_magnitude = 0

        # Reset the number of delayed checks, if applicable
        self.cur_num_first_checks_delayed = 0

        self.long_lived_flag = False

        # Perform adaptive Optimus timeout adjustment
        if self.delay_first_check and self.cur_num_first_checks_delayed < self.num_first_checks_to_delay:
            # If the 5th percentile ttf is much greater than the current timeout, increase the timeout
            # TODO: set values that make sense
            if self.fifth_percentile_ttf > 5 * self.timeout:
                self.cur_num_first_checks_delayed += 1
                self.timeout = self.fifth_percentile_ttf / 5
                if self.cur_num_first_checks_delayed == self.num_first_checks_to_delay:
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

    def simulate_failure(self, time=None):
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

    def simulate_failure(self, time=None):
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

    def simulate_failure(self, time=None):
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
        # If node is not monitored for being in spec, then correctness data is not valid.
        # Set this to off if correctness is not needed, as it greatly speeds up simulation.
        self.monitor_in_spec = kwargs.get('monitor_in_spec', True)
        self.randomize_calibration = kwargs.get('randomize_calibration', False)
        self.nonlinear_drift = kwargs.get('nonlinear_drift', False)
        self.nonlinear_drift_k = kwargs.get('nonlinear_drift_k', 0.02)
        self.nonlinear_drift_n0 = kwargs.get('nonlinear_drift_n0', 200)

        if not self.monitor_in_spec:
            # Warn the user that correctness data is not valid and not monitored
            print(f"WARNING: Node {self.name} is not monitoring in spec. Correctness data is not valid.")

        super().__init__(**kwargs)
        self.parameter_setup(**kwargs)
        # Used to store parameter values before and after calibration
        self.params_before_calibration = {}
        self.params_after_calibration = {}

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

    def nonlinear_coeff(self, time_since_calibration):
        """Returns a drift factor that starts at 0 and asymptotically approaches 1"""
        return 1 / (1 + np.exp(-self.nonlinear_drift_k * (time_since_calibration - self.nonlinear_drift_n0)))

    def drift_parameters(self, time=None):
        if self.nonlinear_drift and time is not None:
            time_since_calibration = time - self.last_calibration
            nonlinear_coeff = self.nonlinear_coeff(time_since_calibration)
        else:
            nonlinear_coeff = 1

        for param in self.parameters:
            # Decide drift direction
            if np.random.uniform() < self.drift_biases[param]:
                direction = 1
            else:
                direction = -1
            drift = direction * self.drift_rates[param] * np.random.uniform() * nonlinear_coeff
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
        Perform the check evaluate results.
        """
        value = self._check_value()
        return value, value > self.threshold

    def calibrate(self, time):
        # Save the parameters right before calibration
        self.params_before_calibration = self.current_params.copy()

        # Reset to initial parameters
        if self.randomize_calibration:
            new_params = {}
            for param in self.parameters:
                optimal_value = self.initial_params[param]
                drift_scale = self.drift_rates[param] * 2  # Defines range
                drift_direction = self.drift_biases[param] >= 0.5  # Expected to be +1 or -1

                # Shape parameter: higher values reduce skew, lower increases asymmetry
                shape = 2.0  # Adjust as needed for desired tail behavior

                if drift_direction:  # Right-tailed gamma (positive drift bias)
                    new_params[param] = gamma.rvs(a=shape, scale=drift_scale / shape) + optimal_value
                else:  # Left-tailed gamma (negative drift bias)
                    new_params[param] = optimal_value - gamma.rvs(a=shape, scale=drift_scale / shape)
            self.current_params = new_params
        else:
            self.current_params = self.initial_params.copy()

        self.params_after_calibration = self.current_params.copy()

        # Calibrate the time
        super().calibrate(time)

    def _check_failure_magnitude(self):
        """
        Check failure magnitude based on how close the value is to the threshold.
        """
        # TODO: This assumes that the value falls below the threshold.
        #   Create an option to have a topline bound as well.
        value = self._check_value()
        if self.threshold - value < 0.:
            return 0
        if self.threshold - value < 0.01:
            return 1
        else:
            return 2

    def simulate_failure(self, time=None):
        # Used every step of the simulation, therefore must include drift
        # Simulate drift
        self.drift_parameters(time)

        if self.monitor_in_spec:
            self.check_data_value, result = self.run_check()
            self.failed = not result
        # self.failure_magnitude = self._check_failure_magnitude()

    def get_parameter_calibration_data(self):
        return self.params_before_calibration, self.params_after_calibration


class Sin2FuncNode(FuncNode):

    def parameter_setup(self, **kwargs):
        # Default values
        defaults = {
            'omega': 2 * np.pi * 70e3,
            'time': 1.0 / 280e3,  # approximately 3.5us gate time
            'delta': 0.0,  # delta for cos2 error term
            'background': 0.0,  # experimental error. Should be < 0

            'threshold': 0.992,  # Acceptable population threshold

            # Drift rate in absolute units. Will be multiplied by a random number between -1 and 1
            'omega_drift_rate': 25077.5 / 75,  # value of 25077.5 leads being off the threshold
            # Bias positive drift. 0.5 is no bias, 0 is always negative, 1 is always positive
            'omega_drift_bias': 0.6,
            'time_drift_rate': 2.03633e-7 / 75,  # 2.03633e-7 leads to being off threshold
            'time_drift_bias': 0.6,
            'delta_drift_rate': 0.0895624 / 75,  # 0.0895624 approximate delta to be off threshold
            'delta_drift_bias': 0.6,
            'background_drift_rate': 0.008 / 75,  # 0.008 leads to being off threshold
            'background_drift_bias': 0.6,
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
            'omega': 0.0,
            'time': 0.0,
            'delta': -100.,
            'background': 0.,  # Background error is positive
        }

        self.parameter_max_values = {
            'omega': np.inf,
            'time': np.inf,
            'delta': np.inf,
            'background': np.inf,
        }

    def sin2_with_error(self):
        omega = self.current_params['omega']
        time = self.current_params['time']
        delta = self.current_params['delta']
        background = self.current_params['background']
        return np.sin(omega * time) ** 2 * np.cos(delta) ** 2 - background

    def _check_value(self):
        """
        Check data at the desired point
        """
        return self.sin2_with_error()


class ExpDecayFuncNode(FuncNode):

    def parameter_setup(self, **kwargs):
        # Default values
        defaults = {
            'amp': 1.0,
            'decay_time': 10.0,  # time in µs
            'background': 0.0,

            'threshold': 0.992,  # Acceptable population threshold. Desire 99.9%

            # Drift rate in absolute units. Will be multiplied by a random number between -1 and 1
            'amp_drift_rate': 7 / 75,
            # Bias positive drift. 0.5 is no bias, 0 is always negative, 1 is always positive
            'amp_drift_bias': 0.6,
            'decay_time_drift_rate': 4.30677 / 75,
            'decay_time_drift_bias': 0.6,
            'background_drift_rate': 0.007 / 75,
            'background_drift_bias': 0.6,
            'time_drift_rate': 20.7944 / 75,
            'time_drift_bias': 0.4
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
            'amp': self.initial_params['amp'],
            'time': 0.,
            'decay_time': self.initial_params['decay_time'],
            'background': 0.,
        }

        self.parameter_max_values = {
            'amp': np.inf,
            'time': self.initial_params['time'],
            'decay_time': np.inf,
            'background': np.inf,
        }

        # Used to store parameter values before and after calibration
        self.params_before_calibration = {}
        self.params_after_calibration = {}

    def exp_decay(self):
        amp = self.current_params['amp']
        time = self.current_params['time']
        decay_time = self.current_params['decay_time']
        background = self.current_params['background']
        # Background must be positive in exp_decay. The higher this value, the worse it is
        return amp * np.exp(-time / decay_time) + background

    def _check_value(self):
        """
        Check the fidelity. Inverse of the population remainder
        """
        return 1 - self.exp_decay()


class DependentExpDecayNode(ExpDecayFuncNode):
    """Func node that depends on another ExpDecayFuncNode. The value of the dependent node is used to determine the
    background value of this node.
    """

    def __init__(self, **kwargs):
        # Must have a dependent node to source the background value
        assert 'dependent_nodes' in kwargs
        assert 'background_node' in kwargs['dependent_nodes']
        # dependent_nodes must be of the type ExpDecayFuncNode
        assert isinstance(kwargs['dependent_nodes']['background_node'], ExpDecayFuncNode)
        super().__init__(**kwargs)

    def parameter_setup(self, **kwargs):
        # Default values
        defaults = {
            'amp': 1.0,
            'decay_time': 10.0,  # time in µs

            'threshold': 0.992,  # Acceptable population threshold. Desire 99.9%

            # Drift rate in absolute units. Will be multiplied by a random number between -1 and 1
            'amp_drift_rate': 7 / 75,  # value of 7 leads to being off the threshold
            # Bias positive drift. 0.5 is no bias, 0 is always negative, 1 is always positive
            'amp_drift_bias': 0.6,
            'decay_time_drift_rate': 4.30677 / 75,  # value of 4.30677 leads to being off the threshold
            'decay_time_drift_bias': 0.6,
            'time_drift_rate': 20.7944 / 75,  # value of 20.7944 leads to being off the threshold
            'time_drift_bias': 0.4
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
        ]
        self.initial_params = {
            'amp': self.amp,
            'time': self.time,
            'decay_time': self.decay_time,
        }
        self.current_params = self.initial_params.copy()
        self.threshold = self.threshold
        self.drift_rates = {
            'amp': self.amp_drift_rate,
            'time': self.time_drift_rate,
            'decay_time': self.decay_time_drift_rate,
        }
        self.drift_biases = {
            'amp': self.amp_drift_bias,
            'time': self.time_drift_bias,
            'decay_time': self.decay_time_drift_bias,
        }
        self.parameter_min_values = {
            'amp': self.initial_params['amp'],
            'time': 0.,
            'decay_time': self.initial_params['decay_time'],
        }

        self.parameter_max_values = {
            'amp': np.inf,
            'time': self.initial_params['time'],
            'decay_time': np.inf,
        }

    def exp_decay(self):
        amp = self.current_params['amp']
        time = self.current_params['time']
        decay_time = self.current_params['decay_time']
        background = self.dependent_nodes['background_node'].exp_decay()
        # Background must be positive in exp_decay. The higher this value, the worse it is

        return amp * np.exp(-time / decay_time) + background / 5


class SPAMBackgroundNode(ExpDecayFuncNode):
    """Func node that simulates checking background dark fideliyt. This value is then used to simulate SPAM error by
    adding its fidelity value as the background value to the sin2 function, worsening its otucome.
    """

    def parameter_setup(self, **kwargs):
        # Default values
        defaults = {
            'amp': 1.0,
            'decay_time': 10.0,  # time in µs
            'background': 0.0,

            'threshold': 0.992,  # Acceptable population threshold. Desire 99.9%

            # Drift rate in absolute units. Will be multiplied by a random number between -1 and 1
            'amp_drift_rate': 7 / 4900,
            # Bias positive drift. 0.5 is no bias, 0 is always negative, 1 is always positive
            'amp_drift_bias': 0.6,
            'decay_time_drift_rate': 4.30677 / 4900,
            'decay_time_drift_bias': 0.6,
            'background_drift_rate': 0.007 / 4900,
            'background_drift_bias': 0.6,
            'time_drift_rate': 20.7944 / 4900,
            'time_drift_bias': 0.4
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
            'amp': self.initial_params['amp'],
            'time': 0.,
            'decay_time': self.initial_params['decay_time'],
            'background': 0.,
        }

        self.parameter_max_values = {
            'amp': np.inf,
            'time': self.initial_params['time'],
            'decay_time': np.inf,
            'background': np.inf,
        }

        # Used to store parameter values before and after calibration
        self.params_before_calibration = {}
        self.params_after_calibration = {}

    def get_background(self):
        return self.exp_decay()


class RabiNode(Sin2FuncNode):
    """This node depends on a SPAMBackgroundNode, used to determine the background value """

    # np.sin(omega * np.pi * time) ** 2 * np.cos(delta) ** 2 - background
    # Time is about 3.5 us to hit the first peak

    def __init__(self, **kwargs):
        # Must have a dependent node to source the Rabi frequency
        assert 'dependent_nodes' in kwargs
        assert 'spam_background_node' in kwargs['dependent_nodes']
        # dependent_nodes must be of the type SPAMBackgroundNode
        assert isinstance(kwargs['dependent_nodes']['spam_background_node'], SPAMBackgroundNode)

        super().__init__(**kwargs)

    def parameter_setup(self, **kwargs):
        # Default values
        defaults = {
            'omega': 2 * np.pi * 70e3,
            'time': 1.0 / 280e3,  # approximately 3.5us gate time
            'delta': 0.0,  # delta for cos2 error term
            'threshold': 0.992,  # Acceptable population threshold
            # Drift rate in absolute units. Will be multiplied by a random number between -1 and 1
            'omega_drift_rate': 25077.5 / 75,  # value of 25077.5 leads being off the threshold
            # Bias positive drift. 0.5 is no bias, 0 is always negative, 1 is always positive
            'omega_drift_bias': 0.6,
            'time_drift_rate': 2.03633e-7 / 75,  # 2.03633e-7 leads to being off threshold
            'time_drift_bias': 0.6,
            'delta_drift_rate': 0.0895624 / 75,  # 0.0895624 approximate delta to be off threshold
            'delta_drift_bias': 0.6,
        }

        # Override defaults with kwargs if provided
        for key, default in defaults.items():
            setattr(self, key, kwargs.get(key, default))

        self.parameters = [
            'omega',
            'time',
            'delta',
        ]
        self.initial_params = {
            'omega': self.omega,
            'time': self.time,
            'delta': self.delta,
        }
        self.current_params = self.initial_params.copy()
        self.threshold = self.threshold
        self.drift_rates = {
            'omega': self.omega_drift_rate,
            'time': self.time_drift_rate,
            'delta': self.delta_drift_rate,
        }
        self.drift_biases = {
            'omega': self.omega_drift_bias,
            'time': self.time_drift_bias,
            'delta': self.delta_drift_bias,
        }
        self.parameter_min_values = {
            'omega': 0.,
            'time': 0.,
            'delta': -np.inf,
        }

        self.parameter_max_values = {
            'omega': np.inf,
            'time': 100.,
            'delta': np.inf,
        }

    def get_rabi_freq(self):
        omega = self.current_params['omega']
        return omega

    def get_tau(self):
        time = self.current_params['time']
        return time

    def sin2_with_error(self):
        omega = self.current_params['omega']
        time = self.current_params['time']
        delta = self.current_params['delta']
        background = self.dependent_nodes[
            'spam_background_node'].get_background()  # Value must be positive, so will be subracted

        return np.sin(omega * time) ** 2 * np.cos(delta) ** 2 - background / 5


class XGateFreqOnlyNode(FuncNode):

    def __init__(self, **kwargs):
        # Must have a dependent node to source the Rabi frequency
        assert 'dependent_nodes' in kwargs
        assert 'rabi_freq_node' in kwargs['dependent_nodes']
        # dependent_nodes must be of the type rabi_frequency_node
        assert type(kwargs['dependent_nodes']['rabi_freq_node']) is RabiFrequencyNode

        super().__init__(**kwargs)

    def parameter_setup(self, **kwargs):
        # Default values
        defaults = {
            'tau': np.pi / (2 * np.pi * 70e3),
            'spin_phase': 0.,  # laser phase
            'threshold': 0.98,  # Acceptable X gate fidelity
            # Drift rate in absolute units. Will be multiplied by a random number between -1 and 1
            'tau_drift_rate': .05 / (2 * np.pi * 70e3),
            # Bias positive drift. 0.5 is no bias, 0 is always negative, 1 is always positive
            'tau_drift_bias': 0.5,
            'spin_phase_drift_rate': 0.05,
            'spin_phase_drift_bias': 0.5,
        }

        # Override defaults with kwargs if provided
        for key, default in defaults.items():
            setattr(self, key, kwargs.get(key, default))

        self.parameters = [
            'tau',
            'spin_phase',
        ]
        self.initial_params = {
            'tau': self.tau,
            'spin_phase': self.spin_phase,
        }
        self.current_params = self.initial_params.copy()
        self.threshold = self.threshold
        self.drift_rates = {
            'tau': self.tau_drift_rate,
            'spin_phase': self.spin_phase_drift_rate,
        }
        self.drift_biases = {
            'tau': self.tau_drift_bias,
            'spin_phase': self.spin_phase_drift_bias,
        }
        self.parameter_min_values = {
            'tau': 0.,
            'spin_phase': -np.pi / 2,
        }

        self.parameter_max_values = {
            'tau': 1.,
            'spin_phase': np.pi / 2,
        }

        # Used to store parameter values before and after calibration
        self.params_before_calibration = {}
        self.params_after_calibration = {}

    def simulate_X_gate_fidelity(self):
        # Get the Rabi frequency from the dependent node
        rabi_freq = self.dependent_nodes['rabi_freq_node'].get_rabi_freq()

        tau = self.current_params['tau']
        spin_phase = self.current_params['spin_phase']
        # The following are technically unused, but must be of the correct shape
        mode_freq = np.array([13849904.48413065, 14128632.55338318, 14355776.36241415,
                              14540002.43438146, 14685826.11757425])
        eta = np.array([0.1, 0.1, 0.1, 0.1, 0.1])
        normal_coeff = np.array(
            [[-1.04541242e-01], [3.01659288e-01], [-5.37653354e-01], [-6.39532387e-01], [4.47213595e-01]])

        # Initial state is |-> to catch phase errors
        init_qubit_state = (qt.fock(2, 1) - qt.fock(2, 0)) / np.sqrt(2)
        sim = ms_gate.Simulator(mode_freq, eta, normal_coeff, tau, 1, rabi_freq, spin_phase_list=spin_phase)
        sim.solve([0], [], sideband=False, carrier=True, init_qubit_state=init_qubit_state)

        # Calculate fidelity of the X gate. X|-> = |->
        final_state = sim.final_qubit_state

        minus_state = (qt.fock(2, 0) - qt.fock(2, 1)).unit()
        # Compute the density matrix of the ideal |-> state
        rho_ideal = minus_state * minus_state.dag()
        # Compute fidelity: F = Tr( sqrt( sqrt(rho_ideal) * rho_actual * sqrt(rho_ideal) ) )^2
        fidelity = qt.fidelity(final_state, rho_ideal)

        return fidelity

    def _check_value(self):
        """
        Get the fidelity of the X gate
        """
        return self.simulate_X_gate_fidelity()


class XGateNode(FuncNode):

    def __init__(self, **kwargs):
        # Must have a dependent node to source the Rabi frequency
        assert 'dependent_nodes' in kwargs
        assert 'rabi_freq_node' in kwargs['dependent_nodes']
        assert 'tau_node' in kwargs['dependent_nodes']
        # dependent_nodes must be of the type rabi_frequency_node
        assert type(kwargs['dependent_nodes']['rabi_freq_node']) is RabiNode
        assert type(kwargs['dependent_nodes']['tau_node']) is RabiNode

        super().__init__(**kwargs)

    def parameter_setup(self, **kwargs):
        # Default values
        defaults = {
            'spin_phase': 0.,  # laser phase
            'threshold': 0.98,  # Acceptable X gate fidelity
            # Drift rate in absolute units. Will be multiplied by a random number between -1 and 1
            # Bias positive drift. 0.5 is no bias, 0 is always negative, 1 is always positive
            'spin_phase_drift_rate': 0.0632 / 50,
            'spin_phase_drift_bias': 0.4,
        }

        # Override defaults with kwargs if provided
        for key, default in defaults.items():
            setattr(self, key, kwargs.get(key, default))

        self.parameters = [
            'spin_phase',
        ]
        self.initial_params = {
            'spin_phase': self.spin_phase,
        }
        self.current_params = self.initial_params.copy()
        self.threshold = self.threshold
        self.drift_rates = {
            'spin_phase': self.spin_phase_drift_rate,
        }
        self.drift_biases = {
            'spin_phase': self.spin_phase_drift_bias,
        }
        self.parameter_min_values = {
            'spin_phase': -np.pi / 2,
        }

        self.parameter_max_values = {
            'spin_phase': np.pi / 2,
        }

        # Used to store parameter values before and after calibration
        self.params_before_calibration = {}
        self.params_after_calibration = {}

    def simulate_X_gate_fidelity(self):
        # Get the Rabi frequency from the dependent node
        rabi_freq = self.dependent_nodes['rabi_freq_node'].get_rabi_freq()
        tau = self.dependent_nodes['tau_node'].get_tau()

        spin_phase = self.current_params['spin_phase']
        # The following are technically unused, but must be of the correct shape
        mode_freq = np.array([13849904.48413065])
        eta = np.array([0.1])
        normal_coeff = np.array([[-1.04541242e-01]])

        # Initial state is |-> to catch phase errors
        init_qubit_state = (qt.fock(2, 1) - qt.fock(2, 0)) / np.sqrt(2)
        sim = ms_gate.Simulator(mode_freq, eta, normal_coeff, tau, 1, rabi_freq, spin_phase_list=spin_phase)
        sim.solve([0], [], sideband=False, carrier=True, init_qubit_state=init_qubit_state)

        # Calculate fidelity of the X gate. X|-> = |->
        final_state = sim.final_qubit_state

        minus_state = (qt.fock(2, 0) - qt.fock(2, 1)).unit()
        # Compute the density matrix of the ideal |-> state
        rho_ideal = minus_state * minus_state.dag()
        # Compute fidelity: F = Tr( sqrt( sqrt(rho_ideal) * rho_actual * sqrt(rho_ideal) ) )^2
        fidelity = qt.fidelity(final_state, rho_ideal)

        return fidelity

    def _check_value(self):
        """
        Get the fidelity of the X gate
        """
        return self.simulate_X_gate_fidelity()


class XGateSimpleNode(FuncNode):

    def parameter_setup(self, **kwargs):
        # Default values
        defaults = {
            'threshold': 0.98,  # Acceptable X gate fidelity

            'omega': 2 * np.pi * 70e3,
            'omega_drift_rate': 25077.5 / 75,  # value of 25077.5 leads being off the threshold
            'omega_drift_bias': 0.6,

            'time': 1.0 / 280e3,  # approximately 3.5us gate time
            'time_drift_rate': 2.03633e-7 / 75,  # 2.03633e-7 leads to being off threshold
            'time_drift_bias': 0.6,

            'spin_phase': 0.,  # laser phase
            'spin_phase_drift_rate': 0.0632 / 50,
            'spin_phase_drift_bias': 0.4,
        }

        # Override defaults with kwargs if provided
        for key, default in defaults.items():
            setattr(self, key, kwargs.get(key, default))

        self.parameters = [
            'omega',
            'time',
            'spin_phase',
        ]
        self.initial_params = {
            'omega': self.omega,
            'time': self.time,
            'spin_phase': self.spin_phase,
        }
        self.current_params = self.initial_params.copy()
        self.threshold = self.threshold
        self.drift_rates = {
            'omega': self.omega_drift_rate,
            'time': self.time_drift_rate,
            'spin_phase': self.spin_phase_drift_rate,
        }
        self.drift_biases = {
            'omega': self.omega_drift_bias,
            'time': self.time_drift_bias,
            'spin_phase': self.spin_phase_drift_bias,
        }
        self.parameter_min_values = {
            'omega': 0.0,
            'time': 0.0,
            'spin_phase': -np.pi / 2,
        }

        self.parameter_max_values = {
            'omega': np.inf,
            'time': np.inf,
            'spin_phase': np.pi / 2,
        }

        # Used to store parameter values before and after calibration
        self.params_before_calibration = {}
        self.params_after_calibration = {}

    def simulate_X_gate_fidelity(self):
        # Get the Rabi frequency from the dependent node
        rabi_freq = self.dependent_nodes['rabi_freq_node'].get_rabi_freq()

        omega = self.current_params['omega']
        time = self.current_params['time']
        spin_phase = self.current_params['spin_phase']

        # The following are technically unused, but must be of the correct shape
        mode_freq = np.array([13849904.48413065])
        eta = np.array([0.1])
        normal_coeff = np.array([[-1.04541242e-01]])

        # Initial state is |-> to catch phase errors
        init_qubit_state = (qt.fock(2, 1) - qt.fock(2, 0)) / np.sqrt(2)
        sim = ms_gate.Simulator(mode_freq, eta, normal_coeff, time, 1, omega, spin_phase_list=spin_phase)
        sim.solve([0], [], sideband=False, carrier=True, init_qubit_state=init_qubit_state)

        # Calculate fidelity of the X gate. X|-> = |->
        final_state = sim.final_qubit_state

        minus_state = (qt.fock(2, 0) - qt.fock(2, 1)).unit()
        # Compute the density matrix of the ideal |-> state
        rho_ideal = minus_state * minus_state.dag()
        # Compute fidelity: F = Tr( sqrt( sqrt(rho_ideal) * rho_actual * sqrt(rho_ideal) ) )^2
        fidelity = qt.fidelity(final_state, rho_ideal)

        return fidelity

    def _check_value(self):
        """
        Get the fidelity of the X gate
        """
        return self.simulate_X_gate_fidelity()
