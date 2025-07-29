import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
ACTIVE_SEEDS_FILE = PROJECT_ROOT / 'data' / 'active_fractal_seeds.json'
REMOVED_SEEDS_FILE = PROJECT_ROOT / 'data' / 'removed_fractal_seeds.json'

def _load_json(filepath: Path):
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

def _save_json(filepath: Path, data: dict):
    """
    Internal helper function to save JSON file.
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def load_all_seeds() -> tuple[dict, dict]:
    """
    Loads all active and removed fractal seeds from JSON files.
    Initializes with empty dictionary if files don't exist.
    
    Returns: 
        tuple: (active_seeds, removed_seeds)
    """
    active_seeds = _load_json(ACTIVE_SEEDS_FILE)
    removed_seeds = _load_json(REMOVED_SEEDS_FILE)
    return active_seeds, removed_seeds

def save_all_seeds(active_seeds: dict, removed_seeds: dict):
    """
    Saves all active and removed fractal seeds to JSON file.
    """
    _save_json(ACTIVE_SEEDS_FILE, active_seeds)
    _save_json(REMOVED_SEEDS_FILE, removed_seeds)

def get_next_seed_id(active_seeds: dict, removed_seeds: dict):
    """
    Generates new sequential seed ID based on existing seeds.
    
    Args: 
        active_seeds (dict)
        removed_seeds (dict)
    Returns: 
        str: Next available unique seed ID formatted 'seed_NNNNN'.
    """
    #Assumes IDs are in format 'seed_NNNNN'
    max_num = 0
    for seed_id in active_seeds.keys():
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

def add_seed(params: dict, 
             active_seeds: dict, 
             removed_seeds: dict
             ) -> str:
    """
    Adds a new fractal seed to active seeds diciontary.
    
    Args:
        params (dict): Dictionary containing image metadata (type, subtype, power, x_span, y_span, x_center, y_center, c_real c_imag, bailout, iterations).
        active_seeds (dict): The dictionary of active seed records.
        removed_seeds (dict): The dictionary of removed seed records.

    Returns:
        str: The ID of the newly added seed.
    """
    new_seed_id = get_next_seed_id(active_seeds, removed_seeds)

    active_seeds[new_seed_id] = {
        'type': params['type'],
        'subtype': params['subtype'],
        'power': params['power'],
        'x_span': params['x_span'],
        'y_span': params['y_span'],
        'x_center': params['x_center'],
        'y_center': params['y_center'],
        'c_real': params['c_real'],
        'c_imag': params['c_imag'],
        'bailout': params['bailout'],
        'iterations': params['iterations']
    }
    save_all_seeds(active_seeds, removed_seeds)
    return new_seed_id

def get_seed_by_id(seed_id: str,
                   active_seeds: dict, 
                   removed_seeds: dict
                   ) -> tuple[dict | None, str | None]:
    """
    Retrieves seed by its ID from either active or removed seeds.

    Args:
        seed_id (str): the ID of the seed to retrieve.
        active_seeds (dict)
        removed_seeds (dict)

    Returns:
        tuple: (seed_data, status) where status is active, removed or None.
    """
    if seed_id in active_seeds:
        return active_seeds[seed_id], 'active'
    elif seed_id in removed_seeds:
        return removed_seeds[seed_id], 'removed'
    return None, None

def remove_seed(seed_id: str, 
                active_seeds: dict, 
                removed_seeds: dict
                ) -> bool:
    """
    Removes seed by its ID from active to removed seeds.

    Args:
        seed_id (str): the ID of the seed to retrieve.
        active_seeds (dict)
        removed_seeds (dict)

    Returns:
        bool: True if seed successfully removed, False otherwise.
    """
    if seed_id in active_seeds:
        seed_data = active_seeds.pop(seed_id)
        removed_seeds[seed_id] = seed_data
        save_all_seeds(active_seeds, removed_seeds)
        return True
    return False

def restore_seed(seed_id: str,
                 active_seeds: dict, 
                 removed_seeds: dict
                 ) -> bool:
    """
    Restores seed by its ID from active to removed seeds.

    Args:
        seed_id (str): the ID of the seed to retrieve.
        active_seeds (dict)
        removed_seeds (dict)

    Returns:
        bool: True if seed successfully restored, False otherwise.
    """       
    if seed_id in removed_seeds:
        seed_data = removed_seeds.pop(seed_id)
        active_seeds[seed_id] = seed_data
        save_all_seeds(active_seeds, removed_seeds)
        return True
    return False

def update_seed(seed_id: str, 
                updates: dict, 
                active_seeds: dict, 
                removed_seeds: dict
                ) -> bool:
    """
    Updates specific fields for an existing fractal seed in the active seeds dictionary.

    Args:
        seed_id (str): The ID of the seed to update.
        updates (dict): A dictionary of key-value pairs representing the fields to update.
                        Only fields present in 'updates' will be modified.
        active_seeds (dict): The dictionary of active seed records.
        removed_seeds (dict): The dictionary of removed seed records.

    Returns:
        bool: True if the seed was found and updated, False otherwise.
    """
    if seed_id not in active_seeds:
        # Optionally check removed_seeds here if allowing updating removed seeds.
        # For now only allow updating active seeds.
        return False

    seed_data = active_seeds[seed_id]
    for key, value in updates.items():
        if key in seed_data: # Only update existing keys to prevent adding arbitrary new fields
            seed_data[key] = value
        else:
            print(f"Warning: Attempted to update non-existent key '{key}' for seed '{seed_id}'. Skipping.")
    
    save_all_seeds(active_seeds, removed_seeds)
    return True

def list_seeds(active_seeds: dict,
               removed_seeds: dict,
               status: str = 'active'
               ) -> dict:
    """
    List seeds based on their status.

    Args:
        active_seeds (dict)
        removed_seeds (dict)
        status (str): 'active', 'removed', or 'all'. Defaults to 'active'.

    Returns:
        dict: A dictionary of seeds based on requested status.
    """

    if status == 'active':
        return active_seeds
    elif status == 'removed':
        return removed_seeds
    elif status == 'all':
        combined = {**active_seeds, **removed_seeds}
        return dict(sorted(combined.items()))
    else:
        print("Invalid status. Please use 'active', 'removed', or 'all'.")
        return {}
