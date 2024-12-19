def validate_wave_data(data):
    """
    Assert that the wave data is correctly formatted.
    Expected format: list of dict with keys 'wave', 'timed_trigger', 'root_nodes', 'submitted_nodes'.
    """
    assert all('wave' in entry and 'timed_trigger' in entry and 'root_nodes' in entry and 'submitted_nodes' in entry
                for entry in data), "Invalid wave_data format."
    assert all(isinstance(entry['wave'], float) and isinstance(entry['timed_trigger'], bool)
                and isinstance(entry['root_nodes'], list) and isinstance(entry['submitted_nodes'], list)
                for entry in data), "Invalid wave_data format."


def validate_check_data(data):
    """
    Assert that the check data is correctly formatted.
    Expected format: list of dict with keys 'node', 'check_type', 'wave', 'failure_magnitude'.
    """
    assert all('node' in entry and 'check_type' in entry and 'wave' in entry and 'failure_magnitude' in entry
                for entry in data), "Invalid check_data format."
    assert all(isinstance(entry['node'], str) and isinstance(entry['check_type'], str) and isinstance(entry['wave'], float)
                and isinstance(entry['failure_magnitude'], int) for entry in data), "Invalid check_data format."