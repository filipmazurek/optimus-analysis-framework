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


def split_data_by_wave(wave_data: list[dict]):
    """
    Sort and split simulation data into sublists where each list begins with a timed_trigger=True entry.
    If the first entry is not timed_trigger=True, it will be ignored.

    :param wave_data: The raw simulation data.
    :return: Sorted and split simulation data.
    """
    validate_wave_data(wave_data)

    #  Sort the by the 'wave' value
    sorted_data = sorted(wave_data, key=lambda x: x['wave'])

    # Split into sublists based on 'timed_trigger=True'
    split_data = []
    current_list = []

    for entry in sorted_data:
        if entry['timed_trigger']:
            # If a new propagation starts, save the current list and start a new one
            if current_list:
                split_data.append(current_list)
            current_list = [entry]  # Start a new list with this entry
        else:
            current_list.append(entry)

    # Append the last propagation step if not empty
    if current_list:
        split_data.append(current_list)

    return split_data


def organize_check_data_by_wave(wave_data, check_data):
    """
    Organize the check_data results by wave.

    :param wave_data: list of dict: The raw simulation data.
    :param check_data: list of dict: The check_data results.
    :return: dict: A dictionary where keys are wave numbers and values are the check_data results for that wave.
    """
    validate_wave_data(wave_data)
    validate_check_data(check_data)

    # Remove all data that is not a timed trigger
    wave_data = [entry for entry in wave_data if entry['timed_trigger']]

    # Sort by the 'wave' value
    sorted_sim_data = sorted(wave_data, key=lambda x: x['wave'])

    # Place all check_data results into the appropriate wave bucket
    organized_results = {}
    for i in range(len(sorted_sim_data)):
        low = sorted_sim_data[i]['wave']
        high = sorted_sim_data[i + 1]['wave'] if i + 1 < len(sorted_sim_data) else float('inf')
        organized_results[low] = [result for result in check_data if low <= result['wave'] < high]

    return organized_results