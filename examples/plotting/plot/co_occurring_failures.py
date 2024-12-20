import sys
import os
# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from plotting.test_data.data import fetch_large_sim_data

from oaf.data_processing import find_co_occurring_failures
from oaf.plot.co_occuring_failures import plot

wave_data, _, graph = fetch_large_sim_data()

# Calculate the co-occurring failures for each wave
co_occurring_data = find_co_occurring_failures(wave_data, graph.nodes())

plot(co_occurring_data, graph.nodes())
