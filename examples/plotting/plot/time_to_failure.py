import networkx as nx
from oaf.plot.time_to_failure import calculate_time_to_failure, plot

import sys
import os
# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from plotting.test_data.data import fetch_large_sim_data

# Fetch sim data®
wave_data, _, graph = fetch_large_sim_data()

time_to_failure = calculate_time_to_failure(wave_data, graph.nodes())
plot(time_to_failure)
