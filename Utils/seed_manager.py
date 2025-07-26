import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CURRENT_SEEDS_FILE = PROJECT_ROOT / 'current_fractal_seeds.json'
REMOVED_SEEDS_FILE = PROJECT_ROOT / 'removed_fractal_seeds.json'

def _load_json(filepath):
    """
    Internal helper function to load JSON file.
    """
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f'Warning: {filepath} is corrupted or empty.')
            return {}
    return {}

def _save_json(filepath, data):
    """
    Internal helper function to save JSON file.
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def load_all_seeds():
    """
    Loads all current and removed fractal seeds from JSON files.
    Initializes with empty dictionary if files don't exist.
    
    Returns: 
        tuple: (current_seeds, removed_seeds)
    """
    current_seeds = _load_json(CURRENT_SEEDS_FILE)
    removed_seeds = _load_json(REMOVED_SEEDS_FILE)
    return current_seeds, removed_seeds

def save_all_seeds(current_seeds, removed_seeds):
    """
    Saves all current and removed fractal seeds to JSON file.
    """
    _save_json(CURRENT_SEEDS_FILE, current_seeds)
    _save_json(REMOVED_SEEDS_FILE, removed_seeds)

def get_next_seed_id(current_seeds, removed_seeds):
    """
    Generates new sequential seed ID based on existing seeds.
    
    Args: 
        current_seeds (dict)
        removed_seeds (dict)
    Returns: 
        str: Next available unique seed ID formatted 'seed_NNNNN'.
    """
    #Assumes IDs are in format 'seed_NNNNN'
    max_num = 0
    for seed_id in current_seeds.keys():
        try:
            num = int(seed_id.split('_')[-1])
            if num > max_num:
                max_num = num
        except (ValueError, IndexError):
            continue
    
    for seed_id in removed_seeds.keys():
        try:
            num = int(seed_id.split('_')[-1])
            if num > max_num:
                max_num = num
        except (ValueError, IndexError):
            continue

    return f'seed_{max_num + 1:05d}'

def add_seed(params, current_seeds, removed_seeds):
    """
    Adds a new fractal seed to current seeds diciontary.
    
    Args:
        params (dict)
        current_seeds (dict)
        removed_seeds (dict)

    Returns:
        str: The ID of the newly added seed.
    """
    new_seed_id = get_next_seed_id(current_seeds, removed_seeds)
    
    # Potentially add logic to filter subtype.

    current_seeds[new_seed_id] = {
        'type': params['type'],
        'subtype': params['subtype'],
        'power': params['power'],
        'x_span': params['x_span'],
        'y_span': params['y_span'],
        'x_center': params['x_center'],
        'y_center': params['y_center'],
        'c_value': params['c_value'],
        'bailout': params['bailout'],
        'iterations': params['iterations']
    }
    save_all_seeds(current_seeds, removed_seeds)
    return new_seed_id

def get_seed_by_id(seed_id, current_seeds, removed_seeds):
    """
    Retrieves seed by its ID from either current or removed seeds.

    Args:
        seed_id (str): the ID of the seed to retrieve.
        current_seeds (dict)
        removed_seeds (dict)

    Returns:
        tuple: (seed_data, status) where status is active, removed or None.
    """
    if seed_id in current_seeds:
        return current_seeds[seed_id], 'current'
    elif seed_id in removed_seeds:
        return removed_seeds[seed_id], 'removed'
    return None, None

def remove_seed(seed_id, current_seeds, removed_seeds):
    """
    Removes seed by its ID from current to removed seeds.

    Args:
        seed_id (str): the ID of the seed to retrieve.
        current_seeds (dict)
        removed_seeds (dict)

    Returns:
        bool: True if seed successfully removed, False otherwise.
    """
    if seed_id in current_seeds:
        seed_data = current_seeds.pop(seed_id)
        removed_seeds[seed_id] = seed_data
        save_all_seeds(current_seeds, removed_seeds)
        return True
    return False

def restore_seed(seed_id, current_seeds, removed_seeds):
    """
    Restores seed by its ID from current to removed seeds.

    Args:
        seed_id (str): the ID of the seed to retrieve.
        current_seeds (dict)
        removed_seeds (dict)

    Returns:
        bool: True if seed successfully restored, False otherwise.
    """       
    if seed_id in removed_seeds:
        seed_data = removed_seeds.pop(seed_id)
        current_seeds[seed_id] = seed_data
        save_all_seeds(current_seeds, removed_seeds)
        return True
    return False

def list_seeds(current_seeds, removed_seeds, status='active'):
    """
    List seeds based on their status.

    Args:
        current_seeds (dict)
        removed_seeds (dict)
        status (str): 'active', 'removed', or 'all'. Defaults to 'active'.

    Returns:
        dict: A dictionary of seeds based on requested status.
    """

    if status == 'active':
        return current_seeds
    elif status == 'removed':
        return removed_seeds
    elif status == 'all':
        combined = {**current_seeds, **removed_seeds}
        return dict(sorted(combined.items()))
    else:
        print("Invalid status. Please use 'active', 'removed', or 'all'.")
        return {}
