import json
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
ACTIVE_IMAGES_FILE = PROJECT_ROOT / 'data' / 'active_fractal_images.json'
REMOVED_IMAGES_FILE = PROJECT_ROOT / 'data' / 'removed_fractal_images.json'
RENDERED_FRACTALS_DIR = PROJECT_ROOT / 'rendered_fractals'
ACTIVE_IMAGES_DIR = RENDERED_FRACTALS_DIR / 'active'
REMOVED_IMAGES_DIR = RENDERED_FRACTALS_DIR / 'removed'
STAGING_IMAGES_DIR = RENDERED_FRACTALS_DIR / 'staging'
ACTIVE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
REMOVED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
STAGING_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

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

def load_all_images() -> tuple[dict, dict]:
    """
    Loads all active and removed fractal image metadata from JSON files.
    Initializes with empty dictionary if files don't exist.
    
    Returns: 
        tuple: (active_images, removed_images)
    """
    active_images = _load_json(ACTIVE_IMAGES_FILE)
    removed_images = _load_json(REMOVED_IMAGES_FILE)
    return active_images, removed_images

def save_all_images(active_images: dict, removed_images: dict):
    """
    Saves all active and removed fractal image metadata to JSON file.
    """
    _save_json(ACTIVE_IMAGES_FILE, active_images)
    _save_json(REMOVED_IMAGES_FILE, removed_images)

def get_next_image_id(active_images: dict, removed_images: dict):
    """
    Generates new sequential image ID based on existing images.
    
    Args: 
        active_images (dict)
        removed_images (dict)
    Returns: 
        str: Next available unique image ID formatted 'image_NNNNNN'.
    """
    #Assumes IDs are in format 'image_NNNNNN'
    max_num = 0
    for image_id in active_images.keys():
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

def get_staging_directory_path() -> Path:
    """
    Returns the Path object for the directory where staged images should be saved.
    """
    return STAGING_IMAGES_DIR

def add_image(params: dict, 
              source_filepath: Path, 
              active_images: dict, 
              removed_images: dict
              ) -> tuple[str, bool]:
    """
    Adds a new fractal image to active images dictionary and moves the physical file.
    
    Args:
        params (dict): Dictionary containing image metadata (seed_id, colormap_name, rendering_type, aesthetic_rating, resolution).
        active_images (dict): The dictionary of active image records.
        removed_images (dict): The dictionary of removed image records.

    Returns:
        tuple (str, bool): A tuple containing the ID of the newly added image and
                           a boolean indicating if the file move was successful.
    """
    new_image_id = get_next_image_id(active_images, removed_images)
    destination_filename = f'{new_image_id}{source_filepath.suffix}'
    destination_filepath = ACTIVE_IMAGES_DIR / destination_filename
    relative_filename = f'active/{destination_filename}'
    file_moved_successfully = False
    try:
        shutil.move(source_filepath, destination_filepath)
        file_moved_successfully = True
    except FileNotFoundError:
        print(f'Warning: Source image file not found at {source_filepath}. Metadata will be added but file could not be moved.')
    except Exception as e:
        print(f'Error moving image file {source_filepath} to {destination_filepath}: {e}')

    active_images[new_image_id] = {
        'seed_id': params['seed_id'],
        'filename': relative_filename, # Convert Path to string for JSON
        'colormap_name': params['colormap_name'],
        'rendering_type': params['rendering_type'],
        'aesthetic_rating': params['aesthetic_rating'],
        'resolution': params['resolution'],
        'file_moved_successfully': file_moved_successfully
    }
    save_all_images(active_images, removed_images)
    return new_image_id, file_moved_successfully

def get_image_by_id(image_id: str,
                    active_images: dict, 
                    removed_images: dict
                    ) -> tuple[dict | None, str | None]:
    """
    Retrieves image by its ID from either active or removed images.

    Args:
        image_id (str): the ID of the image to retrieve.
        active_images (dict)
        removed_images (dict)

    Returns:
        tuple: (image_data, status) where status is active, removed or None.
    """
    if image_id in active_images:
        return active_images[image_id], 'active'
    elif image_id in removed_images:
        return removed_images[image_id], 'removed'
    return None, None

def remove_image(image_id: str, 
                 active_images: dict, 
                 removed_images: dict
                 ) -> bool:
    """
    Removes image by its ID from active to removed images and moves the physical file.

    Args:
        image_id (str): the ID of the image to remove.
        active_images (dict)
        removed_images (dict)

    Returns:
        bool: True if image successfully removed (metadata and file move), False otherwise.
    """
    if image_id not in active_images:
        return False
    
    image_data = active_images.pop(image_id)
    removed_images[image_id] = image_data
    source_filepath = RENDERED_FRACTALS_DIR / image_data['filename']
    destination_filename = Path(image_data['filename']).name 
    destination_filepath = REMOVED_IMAGES_DIR / destination_filename

    file_moved_successfully = False
    try:
        shutil.move(source_filepath, destination_filepath)
        file_moved_successfully = True
        image_data['filename'] = f'removed/{destination_filename}'
        image_data['file_moved_successfully'] = file_moved_successfully
    except FileNotFoundError:
        print(f'Warning: Image file not found at {source_filepath}. Metadata updated but file could not be moved.')
        image_data['file_moved_successfully'] = file_moved_successfully
    except Exception as e:
        print(f"Error moving image file {source_filepath} to {destination_filepath}: {e}")
        image_data['file_moved_successfully'] = file_moved_successfully

    save_all_images(active_images, removed_images)
    return file_moved_successfully

def restore_image(image_id: str,
                  active_images: dict, 
                  removed_images: dict
                  ) -> bool:
    """
    Restores image by its ID from active to removed images.

    Args:
        image_id (str): the ID of the image to retrieve.
        active_images (dict)
        removed_images (dict)

    Returns:
        bool: True if image successfully restored (metadata and file move), False otherwise.
    """       
    if image_id not in removed_images:
        return False
    
    image_data = removed_images.pop(image_id)
    active_images[image_id] = image_data
    source_filepath = RENDERED_FRACTALS_DIR / image_data['filename']
    destination_filename = Path(image_data['filename']).name 
    destination_filepath = ACTIVE_IMAGES_DIR / destination_filename

    file_moved_successfully = False
    try:
        shutil.move(source_filepath, destination_filepath)
        file_moved_successfully = True
        image_data['filename'] = f'active/{destination_filename}'
        image_data['file_moved_successfully'] = file_moved_successfully
    except FileNotFoundError:
        print(f'Warning: Image file not found at {source_filepath}. Metadata updated but file could not be moved.')
        image_data['file_moved_successfully'] = file_moved_successfully
    except Exception as e:
        print(f"Error moving image file {source_filepath} to {destination_filepath}: {e}")
        image_data['file_moved_successfully'] = file_moved_successfully

    save_all_images(active_images, removed_images)
    return file_moved_successfully

def update_image(image_id: str, 
                 updates: dict, 
                 active_images: dict, 
                 removed_images: dict
                 ) -> bool:
    """
    Updates specific fields for an existing fractal image in the active images dictionary.

    Args:
        image_id (str): The ID of the image to update.
        updates (dict): A dictionary of key-value pairs representing the fields to update.
                        Only fields present in 'updates' will be modified.
        active_images (dict): The dictionary of active image records.
        removed_images (dict): The dictionary of removed image records.

    Returns:
        bool: True if the image was found and updated, False otherwise.
    """
    if image_id not in active_images:
        # For now, only allow updating active images.
        return False

    image_data = active_images[image_id]
    for key, value in updates.items():
        if key in image_data: # Only update existing keys to prevent adding arbitrary new fields
            image_data[key] = value
        else:
            print(f"Warning: Attempted to update non-existent key '{key}' for image '{image_id}'. Skipping.")
    
    save_all_images(active_images, removed_images)
    return True

def list_images(
    aesthetic_filter: str = 'all',
    seed_id_filter: str | None = None,
    rendering_type_filter: str | None = None,
    colormap_filter: str | None = None,
    resolution_filter: int | None = None,
    status: str = 'all'
    ) -> tuple[dict, dict]:
    """
    Lists image records based on various filters.

    Args:
        aesthetic_filter (str): 'all', 'human_friendly', 'data_friendly', 'experimental'.
        seed_id_filter (str, optional): Filter by a specific fractal seed ID.
        rendering_type_filter (str, optional): Filter by rendering type.
        colormap_filter (str, optional): Filter by colormap name.
        resolution_filter (int, optional): Filter by image resolution.

    Returns:
        tuple: (filtered_active_images, filtered_removed_images)
            filtered_active_images (dict): A dictionary of filtered active image records, sorted by ID.
            filtered_removed_images (dict): A dictionary of filtered removed image records, sorted by ID.
    """
    active_images, removed_images = load_all_images()
    filtered_active_images = {}
    filtered_removed_images = {}

    def _apply_filters(img_data: dict) -> bool:
        matches_aesthetic = (aesthetic_filter == 'all' or img_data.get('aesthetic_rating') == aesthetic_filter) # Consistency: aesthetic_rating
        matches_seed = (seed_id_filter is None or img_data.get('seed_id') == seed_id_filter)
        matches_rendering_type = (rendering_type_filter is None or img_data.get('rendering_type') == rendering_type_filter)
        matches_colormap = (colormap_filter is None or img_data.get('colormap_name') == colormap_filter)
        matches_resolution = (resolution_filter is None or img_data.get('resolution') == resolution_filter)
        return matches_aesthetic and matches_seed and matches_rendering_type and matches_colormap and matches_resolution

    if status == 'active' or status == 'all':
        for img_id, img_data in active_images.items():
            if _apply_filters(img_data): 
                filtered_active_images[img_id] = img_data

    if status == 'removed' or status == 'all':
        for img_id, img_data in removed_images.items():
            if _apply_filters(img_data): 
                filtered_removed_images[img_id] = img_data
            
    return dict(sorted(filtered_active_images.items())), dict(sorted(filtered_removed_images.items()))
