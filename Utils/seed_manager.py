import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CURRENT_SEEDS_FILE = PROJECT_ROOT / 'current_fractal_seeds.json'
REMOVED_SEEDS_FILE = PROJECT_ROOT / 'removed_fractal_seeds.json'

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
    Loads all current and removed fractal seeds from JSON files.
    Initializes with empty dictionary if files don't exist.
    
    Returns: 
        tuple: (current_seeds, removed_seeds)
    """
    current_seeds = _load_json(CURRENT_SEEDS_FILE)
    removed_seeds = _load_json(REMOVED_SEEDS_FILE)
    return current_seeds, removed_seeds

def save_all_seeds(current_seeds: dict, removed_seeds: dict):
    """
    Saves all current and removed fractal seeds to JSON file.
    """
    _save_json(CURRENT_SEEDS_FILE, current_seeds)
    _save_json(REMOVED_SEEDS_FILE, removed_seeds)

def get_next_seed_id(current_seeds: dict, removed_seeds: dict):
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

def add_seed(params: dict, 
             current_seeds: dict, 
             removed_seeds: dict
             ) -> str:
    """
    Adds a new fractal seed to current seeds diciontary.
    
    Args:
        params (dict): Dictionary containing image metadata (type, subtype, power, x_span, y_span, x_center, y_center, c_value, bailout, iterations).
        current_seeds (dict): The dictionary of current seed records.
        removed_seeds (dict): The dictionary of removed seed records.

    Returns:
        str: The ID of the newly added seed.
    """
    new_seed_id = get_next_seed_id(current_seeds, removed_seeds)

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

def get_seed_by_id(seed_id: str,
                   current_seeds: dict, 
                   removed_seeds: dict
                   ) -> tuple[dict | None, str | None]:
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

def remove_seed(seed_id: str, 
                current_seeds: dict, 
                removed_seeds: dict
                ) -> bool:
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

def restore_seed(seed_id: str,
                 current_seeds: dict, 
                 removed_seeds: dict
                 ) -> bool:
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

def update_seed(seed_id: str, 
                updates: dict, 
                current_seeds: dict, 
                removed_seeds: dict
                ) -> bool:
    """
    Updates specific fields for an existing fractal seed in the current seeds dictionary.

    Args:
        seed_id (str): The ID of the seed to update.
        updates (dict): A dictionary of key-value pairs representing the fields to update.
                        Only fields present in 'updates' will be modified.
        current_seeds (dict): The dictionary of current seed records.
        removed_seeds (dict): The dictionary of removed seed records.

    Returns:
        bool: True if the seed was found and updated, False otherwise.
    """
    if seed_id not in current_seeds:
        # Optionally check removed_seeds here if allowing updating removed seeds.
        # For now only allow updating active seeds.
        return False

    seed_data = current_seeds[seed_id]
    for key, value in updates.items():
        if key in seed_data: # Only update existing keys to prevent adding arbitrary new fields
            seed_data[key] = value
        else:
            print(f"Warning: Attempted to update non-existent key '{key}' for seed '{seed_id}'. Skipping.")
    
    save_all_seeds(current_seeds, removed_seeds)
    return True

def list_seeds(current_seeds: dict,
               removed_seeds: dict,
               status: str = 'active'
               ) -> dict:
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
