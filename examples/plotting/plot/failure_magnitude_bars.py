from oaf.plot.failure_magnitude_bars import plot

import sys
import os

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from plotting.test_data.data import fetch_large_sim_data

_, check_data, graph = fetch_large_sim_data()
nodes = graph.nodes()

plot(check_data, nodes)