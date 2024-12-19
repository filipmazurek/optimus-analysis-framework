from oaf.plot.wave_traceback import plot, prep_data
import sys
import os
# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from plotting.test_data.data import fetch_manual_data

sim_data_num = 3
# Fetch sim data
data, _, node_graph = fetch_manual_data(sim_data_num)

# Plot all waves
prepped_data = prep_data(data)
plot(prepped_data, node_graph)
