import sys
import argparse
from fractal_explorer_vae.cli import renderer
#from fractal_explorer_vae.core import fractal_calcs
from fractal_explorer_vae.core.data_managers import seed_manager
from fractal_explorer_vae.core.data_managers import image_manager
 
 # --- Global Data Stores (Loaded once at startup.) ---
 # These will be passed to manager functions.
active_seeds, removed_seeds = {}, {}
active_images, removed_images = {}, {}

def _load_initial_data():
    """Loads all data from managers at the start of the CLI session."""
    global active_seeds, removed_seeds, active_images, removed_images
    active_seeds, removed_seeds = seed_manager.load_all_seeds()
    active_images, removed_images = image_manager.load_all_images()
    print("Data managers initialized.")

# --- Helper Functions for CLI Commands ---

def _print_seed_details(seed_id: str, seed_data: dict, status: str):
    """Helper to print formatted seed details."""
    print(f"\n--- Seed ID: {seed_id} ({status.capitalize()}) ---")
    for key, value in seed_data.items():
        print(f"  {key.replace('_', ' ').capitalize()}: {value}")
    print("-" * (len(seed_id) + 16))

def _print_image_details(image_id: str, image_data: dict, status: str):
    """Helper to print formatted image details."""
    print(f"\n--- Image ID: {image_id} ({status.capitalize()}) ---")
    for key, value in image_data.items():
        print(f"  {key.replace('_', ' ').capitalize()}: {value}")
    print("-" * (len(image_id) + 16))

# --- CLI Command Handlers ---

def handle_list_seeds(args):
    """Handles the 'list-seeds' command."""
    print(f"Listing seeds (status: {args.status})...")
    seeds_to_list = seed_manager.list_seeds(active_seeds, removed_seeds, args.status)
    if not seeds_to_list:
        print(f"No {args.status} seeds found.")
        return

    for seed_id, seed_data in seeds_to_list.items():
        # Determine status for printing (list_seeds returns combined for 'all')
        status = 'active' if seed_id in active_seeds else 'removed'
        _print_seed_details(seed_id, seed_data, status)

def handle_add_seed(args):
    """Handles the 'add-seed' command."""
    # Collect all parameters from args for the new seed
    print("Attempting to add a new seed...")

    # --- 1. Define Valid Choices (Expand these as your fractal_calcs supports them) ---
    VALID_TYPES = ['Julia', 'Mandelbrot']
    VALID_SUBTYPES = {
        'Julia': ['Standard', 'Multi-Julia', 'Negative-Power-Multi-Julia'],
        'Mandelbrot': ['Standard', 'Multi-Mandelbrot']
    }
    # Add more validation for power, bailout, iterations if needed (e.g., specific ranges)

    # --- 2. Perform Validation Checks ---
    errors = []

    # Validate 'type'
    if args.type not in VALID_TYPES:
        errors.append(f"Invalid fractal type: '{args.type}'. Must be one of {VALID_TYPES}.")

    # Validate 'subtype' based on 'type'
    if args.type in VALID_TYPES and args.subtype not in VALID_SUBTYPES.get(args.type, []):
        errors.append(f"Invalid subtype '{args.subtype}' for fractal type '{args.type}'. Must be one of {VALID_SUBTYPES.get(args.type, ['N/A'])}.")
    
    # Validate 'power'
    if not isinstance(args.power, int) or args.power < 2: # Assuming power must be integer >= 2
        errors.append(f"Invalid power: {args.power}. Must be an integer >= 2.")
    
    # Validate 'iterations'
    if not isinstance(args.iterations, int) or args.iterations <= 0:
        errors.append(f"Invalid iterations: {args.iterations}. Must be a positive integer.")

    # Validate 'bailout'
    if not isinstance(args.bailout, (int, float)) or args.bailout <= 0:
        errors.append(f"Invalid bailout: {args.bailout}. Must be a positive number.")

    # Validate 'c_real' and 'c_imag' (they should be floats due to argparse, but good to check for NaN/inf if relevant)
    import math
    if not (isinstance(args.c_real, (int, float)) and math.isfinite(args.c_real)):
        errors.append(f"Invalid c_real value: {args.c_real}. Must be a finite number.")
    if not (isinstance(args.c_imag, (int, float)) and math.isfinite(args.c_imag)):
        errors.append(f"Invalid c_imag value: {args.c_imag}. Must be a finite number.")

    # Conditional validation for c_real/c_imag (only required for Julia sets)
    if args.type == 'Julia' or args.type == 'Multi-Julia':
        if args.c_real is None or args.c_imag is None:
             errors.append("For Julia sets, --c_real and --c_imag are required.")
    # For Mandelbrot, c_real and c_imag are typically derived from the pixel coordinates, not fixed.

    elif args.type == 'Mandelbrot' and (args.c_real is not None or args.c_imag is not None):
        print("Warning: c_real and c_imag are usually ignored for Mandelbrot sets and derived from pixel coordinates.")


    # If any errors, print them and exit
    if errors:
        print("\nError: Invalid input for adding seed:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
        
    seed_params = {
        'type': args.type,
        'subtype': args.subtype,
        'power': args.power,
        'x_span': args.x_span,
        'y_span': args.y_span,
        'x_center': args.x_center,
        'y_center': args.y_center,
        'c_real': args.c_real,
        'c_imag': args.c_imag,
        'bailout': args.bailout,
        'iterations': args.iterations
    }
    
    new_id = seed_manager.add_seed(seed_params, active_seeds, removed_seeds)
    print(f"Seed '{new_id}' added successfully.")
    _print_seed_details(new_id, active_seeds[new_id], 'active')

def handle_get_seed(args):
    """Handles the 'get-seed' command."""
    seed_data, status = seed_manager.get_seed_by_id(args.seed_id, active_seeds, removed_seeds)
    if seed_data:
        _print_seed_details(args.seed_id, seed_data, status)
    else:
        print(f"Seed with ID '{args.seed_id}' not found.")

def handle_update_seed(args):
    """Handles the 'update-seed' command."""
    updates = {}
    # Dynamically collect updates from args, excluding seed_id and command name
    for key, value in vars(args).items():
        if key not in ['seed_id', 'func'] and value is not None:
            # Special handling for c_value if it's updated via real/imag parts
            if key == 'c_real' or key == 'c_imag':
                # Need to retrieve existing c_value or create a new one
                seed_data, _ = seed_manager.get_seed_by_id(args.seed_id, active_seeds, removed_seeds)
                if not seed_data:
                    print(f"Error: Seed '{args.seed_id}' not found for update.")
                    return
                
                active_c = seed_data.get('c_value', 0+0j) # Default to 0 if not present
                new_c_real = args.c_real if args.c_real is not None else active_c.real
                new_c_imag = args.c_imag if args.c_imag is not None else active_c.imag
                updates['c_value'] = complex(new_c_real, new_c_imag)
            else:
                updates[key] = value

    if not updates:
        print("No fields provided for update.")
        return

    if seed_manager.update_seed(args.seed_id, updates, active_seeds, removed_seeds):
        print(f"Seed '{args.seed_id}' updated successfully.")
        _print_seed_details(args.seed_id, active_seeds[args.seed_id], 'active')
    else:
        print(f"Failed to update seed '{args.seed_id}'. Seed not found or no valid updates.")

def handle_remove_seed(args):
    """Handles the 'remove-seed' command."""
    if seed_manager.remove_seed(args.seed_id, active_seeds, removed_seeds):
        print(f"Seed '{args.seed_id}' successfully moved to removed.")
    else:
        print(f"Failed to remove seed '{args.seed_id}'. It might not exist in active seeds.")

def handle_restore_seed(args):
    """Handles the 'restore-seed' command."""
    if seed_manager.restore_seed(args.seed_id, active_seeds, removed_seeds):
        print(f"Seed '{args.seed_id}' successfully restored to active.")
    else:
        print(f"Failed to restore seed '{args.seed_id}'. It might not exist in removed seeds.")

def handle_list_images(args):
    """Handles the 'list-images' command."""
    print(f"Listing images (status: {args.status})...")
    active_imgs, removed_imgs = image_manager.list_images(
        aesthetic_filter=args.aesthetic_filter,
        seed_id_filter=args.seed_id_filter,
        rendering_type_filter=args.rendering_type_filter,
        colormap_filter=args.colormap_filter,
        resolution_filter=args.resolution_filter
    )
    
    images_to_list = {}
    if args.status == 'active' or args.status == 'all':
        images_to_list.update(active_imgs)
    if args.status == 'removed' or args.status == 'all':
        images_to_list.update(removed_imgs) # Note: if same ID in both, active will be overwritten by removed here. list_images returns sorted dicts already.

    if not images_to_list:
        print(f"No {args.status} images found with the given filters.")
        return

    for image_id, image_data in images_to_list.items():
        status = 'active' if image_id in active_images else 'removed'
        _print_image_details(image_id, image_data, status)


def handle_render_image(args):
    """Handles the 'render-image' command."""
    print(f"Attempting to render image for seed ID: {args.seed_id}...")
    seed_data, status = seed_manager.get_seed_by_id(args.seed_id, active_seeds, removed_seeds)
    
    if not seed_data or status == 'removed':
        print(f"Error: Seed '{args.seed_id}' not found or is removed. Cannot render.")
        return

    # Get staging directory from image_manager
    staging_dir = image_manager.get_staging_directory_path()

    try:
        # Call the renderer to generate and save the image to staging
        output_filepath = renderer.render_fractal_to_file(
            seed_data,
            staging_dir,
            resolution=args.resolution,
            colormap_name=args.colormap # Pass colormap name
        )

        # Prepare metadata for image_manager
        image_params = {
            'seed_id': args.seed_id,
            'colormap_name': args.colormap,
            'rendering_type': args.rendering_type, # This might come from seed or be a new arg
            'aesthetic_rating': args.aesthetic_rating, # This might come from seed or be a new arg
            'resolution': args.resolution
        }
        
        # Add image to manager, which handles moving from staging to active
        new_image_id, move_success = image_manager.add_image(
            image_params, output_filepath, active_images, removed_images
        )

        if move_success:
            print(f"Image '{new_image_id}' rendered and added successfully.")
            _print_image_details(new_image_id, active_images[new_image_id], 'active')
        else:
            print(f"Image '{new_image_id}' metadata added, but file movement failed. Check warnings.")

    except Exception as e:
        print(f"An error occurred during rendering or adding image: {e}")
        # Consider more specific error handling based on renderer's potential exceptions

# --- Main CLI Setup ---

def main():
    _load_initial_data() # Load data once at the start

    parser = argparse.ArgumentParser(
        description="Fractal Explorer CLI: Manage fractal seeds and generated images, and render new fractals.",
        formatter_class=argparse.RawTextHelpFormatter # For better multiline help
    )

    # --- Subparsers for different commands ---
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # --- Seed Management Subcommands ---
    seed_parser = subparsers.add_parser("seed", help="Manage fractal seeds.")
    seed_subparsers = seed_parser.add_subparsers(dest="seed_command", required=True, help="Seed commands")

    # seed list
    seed_list_parser = seed_subparsers.add_parser("list", help="List fractal seeds.")
    seed_list_parser.add_argument(
        "--status",
        type=str,
        choices=['active', 'removed', 'all'],
        default='active',
        help="Filter seeds by status: 'active', 'removed', or 'all'."
    )
    seed_list_parser.set_defaults(func=handle_list_seeds)

    # seed add
    seed_add_parser = seed_subparsers.add_parser("add", help="Add a new fractal seed.")
    seed_add_parser.add_argument("--type", type=str, required=True, help="Fractal type (e.g., Julia, Mandelbrot).")
    seed_add_parser.add_argument("--subtype", type=str, required=False, default='', help="Fractal subtype (e.g., Multi-Julia).")
    seed_add_parser.add_argument("--power", type=int, required=True, help="Power of Z (e.g., 2, 8).")
    seed_add_parser.add_argument("--x_span", type=float, required=True, help="X-axis span (e.g., 4.0).")
    seed_add_parser.add_argument("--y_span", type=float, required=True, help="Y-axis span (e.g., 4.0).")
    seed_add_parser.add_argument("--x_center", type=float, required=True, help="X-axis center (e.g., 0.0).")
    seed_add_parser.add_argument("--y_center", type=float, required=True, help="Y-axis center (e.g., 0.0).")
    seed_add_parser.add_argument("--c_real", type=float, required=True, help="Real part of complex constant 'c'.")
    seed_add_parser.add_argument("--c_imag", type=float, required=True, help="Imaginary part of complex constant 'c'.")
    seed_add_parser.add_argument("--bailout", type=float, required=True, help="Bailout radius (e.g., 2.0).")
    seed_add_parser.add_argument("--iterations", type=int, required=True, help="Maximum iterations (e.g., 600).")
    seed_add_parser.set_defaults(func=handle_add_seed)

    # seed get
    seed_get_parser = seed_subparsers.add_parser("get", help="Get details of a specific seed.")
    seed_get_parser.add_argument("seed_id", type=str, help="ID of the seed to retrieve (e.g., seed_00001).")
    seed_get_parser.set_defaults(func=handle_get_seed)

    # seed update
    seed_update_parser = seed_subparsers.add_parser("update", help="Update fields of an existing seed.")
    seed_update_parser.add_argument("seed_id", type=str, help="ID of the seed to update (e.g., seed_00001).")
    seed_update_parser.add_argument("--type", type=str, help="Fractal type (e.g., Julia, Mandelbrot).")
    seed_update_parser.add_argument("--subtype", type=str, help="Fractal subtype (e.g., Multi-Julia).")
    seed_update_parser.add_argument("--power", type=int, help="Power of Z (e.g., 2, 8).")
    seed_update_parser.add_argument("--x_span", type=float, help="X-axis span (e.g., 4.0).")
    seed_update_parser.add_argument("--y_span", type=float, help="Y-axis span (e.g., 4.0).")
    seed_update_parser.add_argument("--x_center", type=float, help="X-axis center (e.g., 0.0).")
    seed_update_parser.add_argument("--y_center", type=float, help="Y-axis center (e.g., 0.0).")
    seed_update_parser.add_argument("--c_real", type=float, help="Real part of complex constant 'c'.")
    seed_update_parser.add_argument("--c_imag", type=float, help="Imaginary part of complex constant 'c'.")
    seed_update_parser.add_argument("--bailout", type=float, help="Bailout radius (e.g., 2.0).")
    seed_update_parser.add_argument("--iterations", type=int, help="Maximum iterations (e.g., 600).")
    seed_update_parser.set_defaults(func=handle_update_seed)

    # seed remove
    seed_remove_parser = seed_subparsers.add_parser("remove", help="Move a seed to removed status.")
    seed_remove_parser.add_argument("seed_id", type=str, help="ID of the seed to remove.")
    seed_remove_parser.set_defaults(func=handle_remove_seed)

    # seed restore
    seed_restore_parser = seed_subparsers.add_parser("restore", help="Restore a seed from removed to active status.")
    seed_restore_parser.add_argument("seed_id", type=str, help="ID of the seed to restore.")
    seed_restore_parser.set_defaults(func=handle_restore_seed)

    # --- Image Management Subcommands ---
    image_parser = subparsers.add_parser("image", help="Manage generated fractal images.")
    image_subparsers = image_parser.add_subparsers(dest="image_command", required=True, help="Image commands")

    # image list
    image_list_parser = image_subparsers.add_parser("list", help="List fractal images.")
    image_list_parser.add_argument(
        "--status",
        type=str,
        choices=['active', 'removed', 'all'],
        default='active',
        help="Filter images by status: 'active', 'removed', or 'all'."
    )
    image_list_parser.add_argument("--aesthetic_filter", type=str, default='all', help="Filter by aesthetic rating (e.g., 'human_friendly').")
    image_list_parser.add_argument("--seed_id_filter", type=str, help="Filter by associated seed ID.")
    image_list_parser.add_argument("--rendering_type_filter", type=str, help="Filter by rendering type.")
    image_list_parser.add_argument("--colormap_filter", type=str, help="Filter by colormap name.")
    image_list_parser.add_argument("--resolution_filter", type=int, help="Filter by image resolution.")
    image_list_parser.set_defaults(func=handle_list_images)

    # image render (and add)
    image_render_parser = image_subparsers.add_parser("render", help="Render a fractal image from a seed and add it to images.")
    image_render_parser.add_argument("seed_id", type=str, help="ID of the seed to render.")
    image_render_parser.add_argument("--resolution", type=int, default=1024, help="Resolution of the rendered image (e.g., 1024).")
    image_render_parser.add_argument("--colormap", type=str, default='twilight', help="Colormap to use for rendering (e.g., 'viridis', 'magma').")
    image_render_parser.add_argument("--rendering_type", type=str, default='iterations', help="Rendering type (e.g., 'iterations', 'magnitude').")
    image_render_parser.add_argument("--aesthetic_rating", type=str, default='experimental', help="Aesthetic rating for the generated image.")
    image_render_parser.set_defaults(func=handle_render_image)


    # --- Parse args and call handler ---
    args = parser.parse_args()
    
    # Call the appropriate handler function
    if hasattr(args, 'func'):
        args.func(args)
    else:
        # This case should ideally not be reached due to required=True on subparsers
        parser.print_help()

if __name__ == "__main__":
    # This block ensures that _load_initial_data() is called only when main.py is executed directly.
    # When imported (e.g., for testing), it won't run.
    main()