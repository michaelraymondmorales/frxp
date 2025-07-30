import sys
import argparse
from pathlib import Path
import yaml
from fractal_explorer_vae.cli import renderer
from fractal_explorer_vae.core.data_managers import seed_manager
from fractal_explorer_vae.core.data_managers import image_manager
 
 # --- Global Data Stores (Loaded once at startup.) ---
active_seeds, removed_seeds = {}, {}
active_images, removed_images = {}, {}

def _load_initial_data():
    """Loads all data from managers at the start of the CLI session."""
    global active_seeds, removed_seeds, active_images, removed_images
    active_seeds, removed_seeds = seed_manager.load_all_seeds()
    active_images, removed_images = image_manager.load_all_images()
    print("\nData managers initialized.")

# --- Helper Functions for CLI Commands ---

def _print_seed_details(seed_id: str, seed_data: dict, status: str):
    """Helper to print formatted seed details."""
    print(f"\n--- Seed ID: {seed_id} ({status.capitalize()}) ---")
    for key, value in seed_data.items():
        # Special formatting for c_real and c_imag
        if key == 'c_real' or key == 'c_imag':
            print(f"  {key.replace('_', ' ').capitalize()}: {value:.10f}" if value is not None else f"  {key.replace('_', ' ').capitalize()}: None")
        elif key in ["x_center", "y_center", "x_span", "y_span", "bailout"] and isinstance(value, (float, int)):
            print(f"  {key.replace('_', ' ').capitalize()}: {value:.10f}")
        else:
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
        status = 'active' if seed_id in active_seeds else 'removed'
        _print_seed_details(seed_id, seed_data, status)

def handle_add_seed(args):
    """Handles the 'add-seed' command."""
    print("Attempting to add a new seed...")

    # --- 1. Define Valid Choices ---
    VALID_TYPES = ['Julia', 'Multi-Julia', 'Mandelbrot', 'Multi-Mandelbrot']

    # --- 2. Perform Validation Checks ---
    errors = []

    # Validate 'type'
    if args.type not in VALID_TYPES:
        errors.append(f"Invalid fractal type: '{args.type}'. Must be one of {VALID_TYPES}.")
    
    # Validate 'power'
    if not isinstance(args.power, int) or args.power < 2: 
        errors.append(f"Invalid power: {args.power}. Must be an integer >= 2.")
    
    # Validate 'iterations'
    if not isinstance(args.iterations, int) or args.iterations <= 0:
        errors.append(f"Invalid iterations: {args.iterations}. Must be a positive integer.")

    # Validate 'bailout'
    if not isinstance(args.bailout, (int, float)) or args.bailout <= 0:
        errors.append(f"Invalid bailout: {args.bailout}. Must be a positive number.")

    # Conditional validation for c_real/c_imag (only required for Julia or Multi-Julia)
    if args.type in ['Julia', 'Multi-Julia']:
        if args.c_real is None or args.c_imag is None:
             errors.append(f"For '{args.type}' sets, --c_real and --c_imag are required.")
        # If provided, attempt conversion to float for validation
        else:
            try:
                float(args.c_real)
            except ValueError:
                errors.append(f"Invalid c_real value: '{args.c_real}'. Must be a valid number.")
            try:
                float(args.c_imag)
            except ValueError:
                errors.append(f"Invalid c_imag value: '{args.c_imag}'. Must be a valid number.")
    
    # If Mandelbrot is selected and c_real/c_imag are provided (which are usually ignored for Mandelbrot)
    elif args.type in ['Mandelbrot', 'Multi-Mandelbrot']:
        if args.c_real is not None or args.c_imag is not None:
            print(f"Warning: c_real and c_imag are usually ignored for {args.type} sets and derived from pixel coordinates.")

    # If any errors, print them and exit
    if errors:
        print("\nError: Invalid input for adding seed:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1) # Exit with error code
        
    # Pass args directly, seed_manager will map to its internal structure
    seed_params = {
        'type': args.type,
        'subtype': args.subtype,
        'power': args.power,
        'x_span': args.x_span,
        'y_span': args.y_span,
        'x_center': args.x_center,
        'y_center': args.y_center,
        'c_real': args.c_real, # Passed as string/None, seed_manager expects this
        'c_imag': args.c_imag, # Passed as string/None, seed_manager expects this
        'bailout': args.bailout,
        'iterations': args.iterations # Passed as is, seed_manager expects this
    }
    
    new_id = seed_manager.add_seed(seed_params, active_seeds, removed_seeds)
    print(f"Seed '{new_id}' added successfully.")
    # Retrieve the stored seed to print its details accurately from manager's format
    added_seed_data, _ = seed_manager.get_seed_by_id(new_id, active_seeds, removed_seeds)
    if added_seed_data:
        _print_seed_details(new_id, added_seed_data, 'active')

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
    
    # Dynamically collect updates from args.
    for key, value in vars(args).items():
        if key in ['seed_id', 'func', 'command', 'seed_command', 'config']:
            continue
        if value is not None:
            # For c_real and c_imag, attempt conversion for validation before passing
            if key == 'c_real' or key == 'c_imag':
                try:
                    updates[key] = float(value) # Convert to float here for validation
                except ValueError:
                    print(f"Error: Invalid {key} value: '{value}'. Must be a valid number.")
                    sys.exit(1) # Exit if invalid number
            else:
                updates[key] = value # Directly use the key as it matches seed_manager's keys

    if not updates:
        print("No fields provided for update.")
        return

    if seed_manager.update_seed(args.seed_id, updates, active_seeds, removed_seeds):
        print(f"Seed '{args.seed_id}' updated successfully.")
        # Re-fetch the updated data to ensure _print_seed_details gets the latest state
        updated_seed_data, _ = seed_manager.get_seed_by_id(args.seed_id, active_seeds, removed_seeds)
        if updated_seed_data:
            _print_seed_details(args.seed_id, updated_seed_data, 'active')
        else:
            print(f"Warning: Seed '{args.seed_id}' was updated but could not be retrieved for printing details.")
    else:
        print(f"Failed to update seed '{args.seed_id}'. Seed not found or no valid updates were provided.")

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

def handle_purge_seed(args):
    """Handles the 'seed purge' command."""
    seed_id = args.seed_id
    
    # --- Confirmation Prompt (CRITICAL for destructive actions) ---
    print(f"\nWARNING: You are about to permanently purge seed '{seed_id}'.")
    print("This action cannot be undone and will destroy the seed's record.")
    confirmation = input("Type 'yes' to confirm: ").strip().lower()

    if confirmation != 'yes':
        print("Purge cancelled.")
        return

    # Call the manager function
    purged_seed_data, success = seed_manager.purge_seed(seed_id, active_seeds, removed_seeds)

    if success:
        print(f"\nSuccessfully purged seed '{seed_id}'.")
        print("Purged seed details for reference, if needed to re-add:")
        _print_seed_details(seed_id, purged_seed_data, 'purged')
    else:
        print(f"Failed to purge seed '{seed_id}'. See messages above for details.")

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
        # To ensure consistent sorting and avoid overwriting if an ID somehow exists in both
        # (though it shouldn't), it's better to combine and then sort if status is 'all'.
        # For 'removed' only, just use removed_imgs directly.
        if args.status == 'all':
            # Combine and re-sort to ensure consistent output order for 'all'
            combined_images = {**active_imgs, **removed_images} # Use removed_images global
            images_to_list = dict(sorted(combined_images.items()))
        else: # args.status == 'removed'
            images_to_list = removed_images


    if not images_to_list:
        print(f"No {args.status} images found with the given filters.")
        return

    for image_id, image_data in images_to_list.items():
        status = 'active' if image_id in active_images else 'removed'
        _print_image_details(image_id, image_data, status)

def handle_add_image(args):
    """
    Handles the 'image add' command.
    Note: This handler is primarily for adding pre-existing image files to the manager,
    not for rendering new ones (that's `image render`).
    It expects a path to a file already in the staging directory.
    """
    print("Attempting to add an image record...")

    # --- Input Validation ---
    errors = []
    VALID_AESTHETIC_RATINGS = ['human_friendly', 'machine_friendly', 'neutral', 'experimental', '']
    
    if not args.source_filepath:
        errors.append("Source filepath is required to add an image.")
    elif not Path(args.source_filepath).exists():
        errors.append(f"Source file not found at '{args.source_filepath}'.")
    
    # Validate seed_id exists in active or removed seeds
    seed_data, _ = seed_manager.get_seed_by_id(args.seed_id, active_seeds, removed_seeds)
    if not seed_data:
        errors.append(f"Seed ID '{args.seed_id}' not found. An image must be linked to an existing seed.")

    if not args.colormap_name:
        errors.append("Colormap name is required.")
    if not args.rendering_type:
        errors.append("Rendering type is required.")
    if args.aesthetic_rating not in VALID_AESTHETIC_RATINGS:
        errors.append(f"Invalid aesthetic rating: '{args.aesthetic_rating}'. Must be one of {VALID_AESTHETIC_RATINGS}.")
    if not isinstance(args.resolution, int) or args.resolution <= 0:
        errors.append("Resolution must be a positive integer.")

    if errors:
        print("\nError: Invalid input for adding image:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    # Prepare parameters for image_manager.add_image
    image_params = {
        'seed_id': args.seed_id,
        'colormap_name': args.colormap_name,
        'rendering_type': args.rendering_type,
        'aesthetic_rating': args.aesthetic_rating,
        'resolution': args.resolution
    }
    
    source_filepath_obj = Path(args.source_filepath)
    new_image_id, move_success = image_manager.add_image(
        image_params, source_filepath_obj, active_images, removed_images
    )

    if move_success:
        print(f"Image '{new_image_id}' record added and file moved successfully.")
        _print_image_details(new_image_id, active_images[new_image_id], 'active')
    else:
        print(f"Image '{new_image_id}' metadata added, but file movement failed. Check warnings above.")
    # Removed sys.exit(1) from here, as it's a success path

def handle_get_image(args):
    """Handles the 'image get' command."""
    image_data, status = image_manager.get_image_by_id(args.image_id, active_images, removed_images)
    if image_data:
        _print_image_details(args.image_id, image_data, status)
    else:
        print(f"Image with ID '{args.image_id}' not found.")

def handle_update_image(args):
    """Handles the 'image update' command."""
    updates = {}
    # Dynamically collect updates from args, excluding image_id and command name
    for key, value in vars(args).items():
        if key in ['image_id', 'func', 'command', 'image_command', 'config']:
            continue
        if value is not None:
            updates[key] = value

    if not updates:
        print("No fields provided for update.")
        return

    if image_manager.update_image(args.image_id, updates, active_images, removed_images):
        print(f"Image '{args.image_id}' updated successfully.")
        # Re-fetch the updated data to ensure _print_image_details gets the latest state
        updated_image_data, _ = image_manager.get_image_by_id(args.image_id, active_images, removed_images)
        if updated_image_data:
            _print_image_details(args.image_id, updated_image_data, 'active')
        else:
            print(f"Warning: Image '{args.image_id}' was updated but could not be retrieved for printing details.")
    else:
        print(f"Failed to update image '{args.image_id}'. Image not found or no valid updates.")

def handle_remove_image(args):
    """Handles the 'image remove' command."""
    # The image_manager.remove_image function already handles file movement and prints warnings
    if image_manager.remove_image(args.image_id, active_images, removed_images):
        print(f"Image '{args.image_id}' successfully moved to removed status (and file moved).")
    else:
        print(f"Failed to remove image '{args.image_id}'. It might not exist in active images or file movement failed. Check warnings above.")

def handle_restore_image(args):
    """Handles the 'image restore' command."""
    # The image_manager.restore_image function already handles file movement and prints warnings
    if image_manager.restore_image(args.image_id, active_images, removed_images):
        print(f"Image '{args.image_id}' successfully restored to active status (and file moved).")
    else:
        print(f"Failed to restore image '{args.image_id}'. It might not exist in removed images or file movement failed. Check warnings above.")

def handle_purge_image(args):
    """Handles the 'image purge' command."""
    image_id = args.image_id
    
    # --- Confirmation Prompt (CRITICAL for destructive actions) ---
    print(f"\nWARNING: You are about to permanently purge image '{image_id}'.")
    print("This action cannot be undone and will destroy the image's record and physical file.")
    confirmation = input("Type 'yes' to confirm: ").strip().lower()

    if confirmation != 'yes':
        print("Purge cancelled.")
        return

    # Call the manager function
    purged_image_data, success = image_manager.purge_image(image_id, active_images, removed_images)

    if success:
        print(f"\nSuccessfully purged image '{image_id}'.")
        print("Purged image details for reference:")
        _print_image_details(image_id, purged_image_data, 'purged')
        
        if not purged_image_data.get('physical_file_deleted', True):
            print("Note: The physical image file could not be deleted. You may need to remove it manually.")
    else:
        print(f"Failed to purge image '{image_id}'. See messages above for details.")

def handle_render_image(args):
    """Handles the 'render-image' command."""
    print(f"Attempting to render image for seed ID: {args.seed_id}...")
    seed_data, status = seed_manager.get_seed_by_id(args.seed_id, active_seeds, removed_seeds)
    
    if not seed_data or status == 'removed':
        print(f"Error: Seed '{args.seed_id}' not found or is removed. Cannot render.")
        sys.exit(1) # Exit with error code

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
            'rendering_type': args.rendering_type, 
            'aesthetic_rating': args.aesthetic_rating, 
            'resolution': args.resolution
        }
        
        # Add image to manager, which handles moving from staging to active
        new_image_id, move_success = image_manager.add_image(
            image_params, output_filepath, active_images, removed_images
        )

        if move_success:
            print(f"Image '{new_image_id}' record added and file moved successfully.")
            _print_image_details(new_image_id, active_images[new_image_id], 'active')
        else:
            print(f"Image '{new_image_id}' metadata added, but file movement failed. Check warnings.")

    except Exception as e:
        print(f"An error occurred during rendering or adding image: {e}")
        sys.exit(1) # Exit with error code

# --- YAML Script Runner ---
def _run_commands_from_yaml(config_path: Path):
    """
    Reads a YAML configuration file and executes CLI commands defined within it.
    """
    if not config_path.exists():
        print(f"Error: YAML configuration file not found at '{config_path}'.")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file '{config_path}': {e}")
        sys.exit(1)

    if 'commands' not in config or not isinstance(config['commands'], list):
        print(f"Error: YAML file '{config_path}' must contain a 'commands' list at the top level.")
        sys.exit(1)

    print(f"\n--- Executing commands from YAML: {config_path} ---")
    
    # Load initial data once for the entire batch of commands
    _load_initial_data() 

    for i, cmd_def in enumerate(config['commands']):
        print(f"\n--- Running Command {i+1}: {cmd_def.get('command')} {cmd_def.get('subcommand')} ---")
        
        command = cmd_def.get('command')
        subcommand = cmd_def.get('subcommand')
        args_dict = cmd_def.get('args', {})

        if not command or not subcommand:
            print(f"Skipping command {i+1}: 'command' and 'subcommand' are required.")
            continue

        # Construct argv list for the command
        cmd_argv = [command, subcommand]
        for arg_name, arg_value in args_dict.items():
            # Crucial: Only append arguments if their value is not None.
            # This prevents 'None' string from being passed for optional args.
            if arg_value is not None:
                cmd_argv.append(f"--{arg_name}")
                cmd_argv.append(str(arg_value)) # Convert to string for argparse
        
        try:
            # Call the main function with the specific command's argv
            # Pass load_initial_data=False as data is already loaded
            main(argv=cmd_argv, load_initial_data=False)
        except SystemExit as e:
            # Catch SystemExit from individual command handlers
            if e.code != 0: # Only report if it's an error exit
                print(f"Command {i+1} failed with exit code {e.code}.")
            # Do not re-exit the entire script here, allow the loop to continue
        except Exception as e:
            print(f"An unexpected error occurred during command {i+1}: {e}")
            # Do not re-exit the entire script here, allow the loop to continue

    print(f"\n--- Finished executing commands from YAML: {config_path} ---")


# --- Main CLI Setup ---

def main(argv=None, load_initial_data=True): # Modified signature
    if load_initial_data: # Conditionally load data
        _load_initial_data()

    # If argv is None, it means main was called directly without arguments (e.g., from __main__ block
    # when --config was not present), so use sys.argv[1:].
    # If argv is provided (e.g., from _run_commands_from_yaml), use that.
    if argv is None: 
        argv = sys.argv[1:] 

    parser = argparse.ArgumentParser(
        description="Fractal Explorer CLI: Manage fractal seeds and generated images, and render new fractals.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Add the --config argument directly to the main parser
    parser.add_argument(
        '--config',
        type=Path,
        help="Path to a YAML configuration file for batch command execution."
    )

    # --- Subparsers for different commands ---
    # Set required=False for the main subparsers, as --config can be used instead
    subparsers = parser.add_subparsers(dest="command", help="Available commands") 

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
    seed_add_parser.add_argument("--c_real", type=str, required=False, help="Real part of complex constant 'c'.")
    seed_add_parser.add_argument("--c_imag", type=str, required=False, help="Imaginary part of complex constant 'c'.")
    seed_add_parser.add_argument("--bailout", type=float, required=True, help="Bailout radius (e.g., 2.0).")
    seed_add_parser.add_argument("--iterations", type=int, required=True, help="Maximum iterations (e.g., 600).")
    seed_add_parser.set_defaults(func=handle_add_seed)

    # seed get (now takes --seed_id as named argument)
    seed_get_parser = seed_subparsers.add_parser("get", help="Get details of a specific seed.")
    seed_get_parser.add_argument("--seed_id", type=str, required=True, help="ID of the seed to retrieve (e.g., seed_00001).")
    seed_get_parser.set_defaults(func=handle_get_seed)

    # seed update (now takes --seed_id as named argument, c_real/c_imag type is str)
    seed_update_parser = seed_subparsers.add_parser("update", help="Update fields of an existing seed.")
    seed_update_parser.add_argument("--seed_id", type=str, required=True, help="ID of the seed to update (e.g., seed_00001).")
    seed_update_parser.add_argument("--type", type=str, help="Fractal type (e.g., Julia, Mandelbrot).")
    seed_update_parser.add_argument("--subtype", type=str, help="Fractal subtype (e.g., Multi-Julia).")
    seed_update_parser.add_argument("--power", type=int, help="Power of Z (e.g., 2, 8).")
    seed_update_parser.add_argument("--x_span", type=float, help="X-axis span (e.g., 4.0).")
    seed_update_parser.add_argument("--y_span", type=float, help="Y-axis span (e.g., 4.0).")
    seed_update_parser.add_argument("--x_center", type=float, help="X-axis center (e.g., 0.0).")
    seed_update_parser.add_argument("--y_center", type=float, help="Y-axis center (e.g., 0.0).")
    seed_update_parser.add_argument("--c_real", type=str, help="Real part of complex constant 'c'.")
    seed_update_parser.add_argument("--c_imag", type=str, help="Imaginary part of complex constant 'c'.")
    seed_update_parser.add_argument("--bailout", type=float, help="Bailout radius (e.g., 2.0).")
    seed_update_parser.add_argument("--iterations", type=int, help="Maximum iterations (e.g., 600).")
    seed_update_parser.set_defaults(func=handle_update_seed)

    # seed remove (now takes --seed_id as named argument)
    seed_remove_parser = seed_subparsers.add_parser("remove", help="Move a seed to removed status.")
    seed_remove_parser.add_argument("--seed_id", type=str, required=True, help="ID of the seed to remove.")
    seed_remove_parser.set_defaults(func=handle_remove_seed)

    # seed restore (now takes --seed_id as named argument)
    seed_restore_parser = seed_subparsers.add_parser("restore", help="Restore a seed from removed to active status.")
    seed_restore_parser.add_argument("--seed_id", type=str, required=True, help="ID of the seed to restore.")
    seed_restore_parser.set_defaults(func=handle_restore_seed)

    # seed purge (now takes --seed_id as named argument)
    seed_purge_parser = seed_subparsers.add_parser("purge", help="Permanently delete a seed from removed status.")
    seed_purge_parser.add_argument("--seed_id", type=str, required=True, help="ID of the seed to purge.")
    seed_purge_parser.set_defaults(func=handle_purge_seed)
    
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

    # image add (now takes --source_filepath as named argument)
    image_add_parser = image_subparsers.add_parser("add", help="Add an existing image file to the image manager.")
    image_add_parser.add_argument("--source_filepath", type=str, required=True, help="Path to the image file to add (e.g., in staging directory).")
    image_add_parser.add_argument("--seed_id", type=str, required=True, help="ID of the seed associated with this image.")
    image_add_parser.add_argument("--colormap_name", type=str, required=True, help="Colormap used for rendering.")
    image_add_parser.add_argument("--rendering_type", type=str, required=True, help="Type of rendering (e.g., 'iterations', 'angle_map').")
    image_add_parser.add_argument("--aesthetic_rating", type=str, default="", help="Aesthetic rating for the image (e.g., 'human_friendly', 'neutral').")
    image_add_parser.add_argument("--resolution", type=int, required=True, help="Resolution of the image.")
    image_add_parser.set_defaults(func=handle_add_image)

    # image get (now takes --image_id as named argument)
    image_get_parser = image_subparsers.add_parser("get", help="Get details of a specific image.")
    image_get_parser.add_argument("--image_id", type=str, required=True, help="ID of the image to retrieve (e.g., image_000001).")
    image_get_parser.set_defaults(func=handle_get_image)

    # image update (now takes --image_id as named argument)
    image_update_parser = image_subparsers.add_parser("update", help="Update fields of an existing image.")
    image_update_parser.add_argument("--image_id", type=str, required=True, help="ID of the image to update (e.g., image_000001).")
    image_update_parser.add_argument("--seed_id", type=str, help="New seed ID associated with this image.")
    image_update_parser.add_argument("--colormap_name", type=str, help="New colormap used for rendering.")
    image_update_parser.add_argument("--rendering_type", type=str, help="New type of rendering.")
    image_update_parser.add_argument("--aesthetic_rating", type=str, help="New aesthetic rating.")
    image_update_parser.add_argument("--resolution", type=int, help="New resolution of the image.")
    image_update_parser.set_defaults(func=handle_update_image)

    # image remove (now takes --image_id as named argument)
    image_remove_parser = image_subparsers.add_parser("remove", help="Move an image to removed status.")
    image_remove_parser.add_argument("--image_id", type=str, required=True, help="ID of the image to remove.")
    image_remove_parser.set_defaults(func=handle_remove_image)

    # image restore (now takes --image_id as named argument)
    image_restore_parser = image_subparsers.add_parser("restore", help="Restore an image from removed to active status.")
    image_restore_parser.add_argument("--image_id", type=str, required=True, help="ID of the image to restore.")
    image_restore_parser.set_defaults(func=handle_restore_image)

    # image purge (now takes --image_id as named argument)
    image_purge_parser = image_subparsers.add_parser("purge", help="Permanently delete an image from removed status.")
    image_purge_parser.add_argument("--image_id", type=str, required=True, help="ID of the image to purge.")
    image_purge_parser.set_defaults(func=handle_purge_image)

    # image render (now takes --seed_id as named argument)
    image_render_parser = image_subparsers.add_parser("render", help="Render a fractal image from a seed and add it to images.")
    image_render_parser.add_argument("--seed_id", type=str, required=True, help="ID of the seed to render.")
    image_render_parser.add_argument("--resolution", type=int, default=1024, help="Resolution of the rendered image (e.g., 1024).")
    image_render_parser.add_argument("--colormap", type=str, default='twilight', help="Colormap to use for rendering (e.g., 'viridis', 'magma').")
    image_render_parser.add_argument("--rendering_type", type=str, default='iterations', help="Rendering type (e.g., 'iterations', 'magnitude').")
    image_render_parser.add_argument("--aesthetic_rating", type=str, default='experimental', help="Aesthetic rating for the generated image.")
    image_render_parser.set_defaults(func=handle_render_image)


    # --- Parse args and call handler ---
    # Parse the provided argv, not sys.argv directly
    args = parser.parse_args(argv) 
    
    # Conditional logic for --config or command
    if args.config:
        _run_commands_from_yaml(args.config)
    elif args.command is None: # No command and no --config
        parser.print_help()
        sys.exit(1) # Exit with error code if no command is given
    else: # A command was given
        args.func(args)


if __name__ == "__main__":
    # This block is for when the script is run directly from the command line
    # (e.g., `python main.py --config ...` or `fex --config ...`)
    
    # Pass all arguments after the script name to main for parsing
    main(argv=sys.argv[1:], load_initial_data=True)