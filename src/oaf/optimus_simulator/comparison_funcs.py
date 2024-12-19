import numpy as np
from spa.core import spa, smc
from spa.properties import ThresholdProperty


# Classic comparison Functions
def mean_greater_than(data, threshold):
    return np.mean(data) > threshold


# SPA Comparison Functions
def create_spa_greater_than(proportion, confidence):
    smc_direction = '>'

    def smc_comparison_func(data, threshold):
        smc_result = smc(data,
                         ThresholdProperty(threshold=threshold, op=smc_direction),
                         prob_threshold=proportion,
                         confidence=confidence,
                         continuous=True)
        return smc_result.result

    return smc_comparison_func
