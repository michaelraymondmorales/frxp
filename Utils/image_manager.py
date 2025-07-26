import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CURRENT_IMAGES_FILE = PROJECT_ROOT / 'current_fractal_images.json'
REMOVED_IMAGES_FILE = PROJECT_ROOT / 'removed_fractal_images.json'

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

def load_all_images():
    """
    Loads all current and removed fractal image metadata from JSON files.
    Initializes with empty dictionary if files don't exist.
    
    Returns: 
        tuple: (current_images, removed_images)
    """
    current_images = _load_json(CURRENT_IMAGES_FILE)
    removed_images = _load_json(REMOVED_IMAGES_FILE)
    return current_images, removed_images

def save_all_images(current_images, removed_images):
    """
    Saves all current and removed fractal image metadata to JSON file.
    """
    _save_json(CURRENT_IMAGES_FILE, current_images)
    _save_json(REMOVED_IMAGES_FILE, removed_images)

def get_next_image_id(current_images, removed_images):
    """
    Generates new sequential image ID based on existing images.
    
    Args: 
        current_images (dict)
        removed_images (dict)
    Returns: 
        str: Next available unique image ID formatted 'image_NNNNN'.
    """
    #Assumes IDs are in format 'image_NNNNNN'
    max_num = 0
    for image_id in current_images.keys():
        try:
            num = int(image_id.split('_')[-1])
            if num > max_num:
                max_num = num
        except (ValueError, IndexError):
            continue
    
    for image_id in removed_images.keys():
        try:
            num = int(image_id.split('_')[-1])
            if num > max_num:
                max_num = num
        except (ValueError, IndexError):
            continue

    return f'image_{max_num + 1:06d}'

def add_image(params, current_images, removed_images):
    """
    Adds a new fractal image to current images dictionary.
    
    Args:
        params (dict): Dictionary containing image metadata (seed_id, filename, colormap_name, rendering_type, aesthetic_rating, resolution).
        current_images (dict): The dictionary of current image records.
        removed_images (dict): The dictionary of removed image records.

    Returns:
        str: The ID of the newly added image.
    """
    new_image_id = get_next_image_id(current_images, removed_images)

    current_images[new_image_id] = {
        'seed_id': params['seed_id'],
        'filename': params['filename'], # Convert Path to string for JSON
        'colormap_name': params['colormap_name'],
        'rendering_type': params['rendering_type'],
        'aesthetic_rating': params['aesthetic_rating'],
        'resolution': params['resolution']
    }
    save_all_images(current_images, removed_images)
    return new_image_id

def get_image_by_id(image_id, current_images, removed_images):
    """
    Retrieves image by its ID from either current or removed images.

    Args:
        image_id (str): the ID of the image to retrieve.
        current_images (dict)
        removed_images (dict)

    Returns:
        tuple: (image_data, status) where status is active, removed or None.
    """
    if image_id in current_images:
        return current_images[image_id], 'current'
    elif image_id in removed_images:
        return removed_images[image_id], 'removed'
    return None, None

def remove_image(image_id, current_images, removed_images):
    """
    Removes image by its ID from current to removed images.

    Args:
        image_id (str): the ID of the image to retrieve.
        current_images (dict)
        removed_images (dict)

    Returns:
        bool: True if image successfully removed, False otherwise.
    """
    if image_id in current_images:
        image_data = current_images.pop(image_id)
        removed_images[image_id] = image_data
        save_all_images(current_images, removed_images)
        return True
    return False

def restore_image(image_id, current_images, removed_images):
    """
    Restores image by its ID from current to removed images.

    Args:
        image_id (str): the ID of the image to retrieve.
        current_images (dict)
        removed_images (dict)

    Returns:
        bool: True if image successfully restored, False otherwise.
    """       
    if image_id in removed_images:
        image_data = removed_images.pop(image_id)
        current_images[image_id] = image_data
        save_all_images(current_images, removed_images)
        return True
    return False

def list_images(
    aesthetic_filter: str = 'all',
    seed_id_filter: str | None = None,
    rendering_type_filter: str | None = None,
    colormap_filter: str | None = None,
    resolution_filter: int | None = None
) -> dict:
    """
    Lists image records based on various filters.

    Args:
        aesthetic_filter (str): 'all', 'human_friendly', 'data_friendly', 'experimental'.
        seed_id_filter (str, optional): Filter by a specific fractal seed ID.
        rendering_type_filter (str, optional): Filter by rendering type.
        colormap_filter (str, optional): Filter by colormap name.
        resolution_filter (int, optional): Filter by image resolution.

    Returns:
        tuple: (filtered_current_images, filtered_removed_images)
            filtered_current_images (dict): A dictionary of filtered current image records, sorted by ID.
            filtered_removed_images (dict): A dictionary of filtered removed image records, sorted by ID.
    """
    current_images, removed_images = load_all_images()
    filtered_current_images = {}
    filtered_removed_images = {}

    def _apply_filters(img_data):
        matches_aesthetic = (aesthetic_filter == 'all' or img_data.get('aesthetic_rating') == aesthetic_filter) # Consistency: aesthetic_rating
        matches_seed = (seed_id_filter is None or img_data.get('seed_id') == seed_id_filter)
        matches_rendering_type = (rendering_type_filter is None or img_data.get('rendering_type') == rendering_type_filter)
        matches_colormap = (colormap_filter is None or img_data.get('colormap_name') == colormap_filter)
        matches_resolution = (resolution_filter is None or img_data.get('resolution') == resolution_filter)
        return matches_aesthetic and matches_seed and matches_rendering_type and matches_colormap and matches_resolution

    for img_id, img_data in current_images.items():
        if _apply_filters(img_data):
            filtered_current_images[img_id] = img_data

    for img_id, img_data in removed_images.items():
        if _apply_filters(img_data):
            filtered_removed_images[img_id] = img_data
            
    return dict(sorted(filtered_current_images.items())), dict(sorted(filtered_removed_images.items()))
