from oaf.data_processing import split_data_by_wave
from oaf.plot.base_failures_heatmap import plot_combined_heatmap
from oaf.base_failure import find_base_failures

import sys
import os
# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from plotting.test_data.data import fetch_large_sim_data


wave_data, _, graph = fetch_large_sim_data()
base_failure_stats = find_base_failures(wave_data, graph)

nodes = graph.nodes()

plot_combined_heatmap(base_failure_stats, graph)
