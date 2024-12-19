from oaf.plot.node_importance_score import calculate_check_scores, plot_check_scores

import sys
import os
# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from plotting.test_data.data import fetch_large_sim_data

# Fetch sim data
wave_data, check_data, node_graph = fetch_large_sim_data()

# Calculate check scores
check_scores = calculate_check_scores(wave_data, check_data, node_graph)

# Plot check scores
plot_check_scores(check_scores, node_graph.nodes())