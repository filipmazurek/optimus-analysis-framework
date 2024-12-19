from oaf.base_failure import find_base_failures, find_mean_failure_chain_length
from oaf.plot.base_failure_chain_length import plot

import sys
import os
# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from plotting.test_data.data import fetch_large_sim_data


data, _, graph = fetch_large_sim_data()
base_failure_stats = find_base_failures(data, graph)

failure_chain_lengths = find_mean_failure_chain_length(base_failure_stats, graph)
plot(failure_chain_lengths)
