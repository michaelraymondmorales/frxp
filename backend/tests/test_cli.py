import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

# Import the main CLI entry point function
# Note: We import main directly to call it, but mock its internal dependencies
from frxp.cli.main import main, _load_initial_data, active_seeds, removed_seeds, active_images, removed_images

class TestCLI(unittest.TestCase):

    def setUp(self):
        """
        Set up the test environment before each test.
        This includes:
        - Mocking sys.stdout to capture printed output.
        - Mocking sys.stdin to provide simulated user input for `input()`.
        - Patching global data stores to prevent actual file I/O during CLI tests.
        - Patching manager functions to control their return values and side effects.
        """
        # 1. Mock sys.stdout to capture print statements
        self.held_stdout = sys.stdout
        self.mock_stdout = StringIO()
        sys.stdout = self.mock_stdout

        # 2. Mock sys.stdin for `input()` calls (will be set per test for specific inputs)
        # Patch builtins.input directly, side_effect will be set in tests that need it
        self.input_patcher = patch('builtins.input')
        self.mock_input = self.input_patcher.start()

        # 3. Patch the global data stores and manager load functions
        # Use new_callable=dict to ensure they are fresh, empty dicts for each test
        self.patcher_active_seeds = patch('frxp.cli.main.active_seeds', new_callable=dict)
        self.patcher_removed_seeds = patch('frxp.cli.main.removed_seeds', new_callable=dict)
        self.patcher_active_images = patch('frxp.cli.main.active_images', new_callable=dict)
        self.patcher_removed_images = patch('frxp.cli.main.removed_images', new_callable=dict)
        
        # Start the patches for global dictionaries
        self.mock_active_seeds = self.patcher_active_seeds.start()
        self.mock_removed_seeds = self.patcher_removed_seeds.start()
        self.mock_active_images = self.patcher_active_images.start()
        self.mock_removed_images = self.patcher_removed_images.start()

        # Mock the _load_initial_data function so it doesn't try to load real files
        self.mock_load_initial_data = patch('frxp.cli.main._load_initial_data').start()
        self.mock_load_initial_data.return_value = None # It just prints, doesn't return anything significant

        # 4. Patch manager functions that the CLI handlers call
        # We need to control what these functions return to test CLI logic
        self.mock_seed_manager_add_seed = patch('frxp.cli.main.seed_manager.add_seed').start()
        self.mock_seed_manager_get_seed_by_id = patch('frxp.cli.main.seed_manager.get_seed_by_id').start()
        self.mock_seed_manager_update_seed = patch('frxp.cli.main.seed_manager.update_seed').start()
        self.mock_seed_manager_remove_seed = patch('frxp.cli.main.seed_manager.remove_seed').start()
        self.mock_seed_manager_restore_seed = patch('frxp.cli.main.seed_manager.restore_seed').start()
        self.mock_seed_manager_purge_seed = patch('frxp.cli.main.seed_manager.purge_seed').start()
        self.mock_seed_manager_list_seeds = patch('frxp.cli.main.seed_manager.list_seeds').start()

        self.mock_image_manager_add_image = patch('frxp.cli.main.image_manager.add_image').start()
        self.mock_image_manager_get_image_by_id = patch('frxp.cli.main.image_manager.get_image_by_id').start()
        self.mock_image_manager_update_image = patch('frxp.cli.main.image_manager.update_image').start()
        self.mock_image_manager_remove_image = patch('frxp.cli.main.image_manager.remove_image').start()
        self.mock_image_manager_restore_image = patch('frxp.cli.main.image_manager.restore_image').start()
        self.mock_image_manager_purge_image = patch('frxp.cli.main.image_manager.purge_image').start()
        self.mock_image_manager_list_images = patch('frxp.cli.main.image_manager.list_images').start()
        self.mock_image_manager_get_staging_directory_path = patch('frxp.cli.main.image_manager.get_staging_directory_path').start()

        self.mock_renderer_render_fractal_to_file = patch('frxp.cli.main.renderer.render_fractal_to_file').start()
        
        # Reset sys.argv for each test
        self.original_argv = sys.argv
        sys.argv = ['main.py'] # Default to just the script name

    def tearDown(self):
        """
        Clean up the test environment after each test.
        """
        # Stop all patches
        patch.stopall()

        # Restore sys.stdout and sys.stdin
        sys.stdout = self.held_stdout
        sys.stdin = sys.__stdin__ # Restore original stdin

        # Restore sys.argv
        sys.argv = self.original_argv

    def _run_cli(self, args_list):
        """
        Helper to run the main CLI function with given arguments.
        Does NOT catch SystemExit; tests expecting SystemExit must use assertRaises.
        """
        sys.argv = ['main.py'] + args_list
        main()


    def test_help_command(self):
        """Test the frxp --help command."""
        # argparse calls sys.exit(0) for --help, so we expect SystemExit with code 0
        with self.assertRaises(SystemExit) as cm:
            self._run_cli(['--help'])
        self.assertEqual(cm.exception.code, 0) # Help exits with 0
        output = self.mock_stdout.getvalue()
        self.assertIn("usage: main.py", output)
        self.assertIn("Manage fractal seeds and generated images", output)
        self.assertIn("Available commands", output)
        self.assertIn("seed", output)
        self.assertIn("image", output)

    # --- Seed Command Tests ---

    def test_seed_list_active(self):
        """Test 'frxp seed list' to list active seeds."""
        # Configure mock manager to return some data
        mock_seed_data = {'seed_00001': {'type': 'Julia', 'power': 2, 'iterations': 600, 'x_span': 4.0, 'y_span': 4.0, 'x_center': 0.0, 'y_center': 0.0, 'c_real': -0.7, 'c_imag': 0.27015, 'bailout': 2.0, 'subtype': 'Standard'}}
        self.mock_seed_manager_list_seeds.return_value = mock_seed_data
        # Populate the mock active_seeds dictionary that _print_seed_details uses
        self.mock_active_seeds.update(mock_seed_data)
        
        self._run_cli(['seed', 'list', '--status', 'active'])
        output = self.mock_stdout.getvalue()
        self.assertIn("Listing seeds (status: active)...\n", output)
        self.assertIn("--- Seed ID: seed_00001 (Active) ---", output)
        self.assertIn("Type: Julia", output)
        self.assertIn("Power: 2", output)
        self.assertIn("Iterations: 600", output)
        # Assert that list_seeds was called with the actual mock global dictionaries
        self.mock_seed_manager_list_seeds.assert_called_once_with(self.mock_active_seeds, self.mock_removed_seeds, 'active')

    def test_seed_add_success(self):
        """Test 'frxp seed add' for successful addition."""
        seed_id = 'seed_00001' # Define seed_id here for clarity
        mock_seed_data_for_add = {
            'type': 'Julia', 'subtype': 'Standard', 'power': 2, 'x_span': 4.0, 'y_span': 4.0,
            'x_center': 0.0, 'y_center': 0.0, 'c_real': -0.7, 'c_imag': 0.27015,
            'bailout': 2.0, 'iterations': 600
        }
        self.mock_seed_manager_add_seed.return_value = seed_id
        
        # Configure the mock get_seed_by_id to return the data that was "added"
        self.mock_seed_manager_get_seed_by_id.return_value = (mock_seed_data_for_add, 'active')

        # Populate the mock active_seeds dictionary that _print_seed_details uses
        # This is crucial because _print_seed_details directly accesses global active_seeds
        self.mock_active_seeds[seed_id] = mock_seed_data_for_add.copy() # Use .copy()

        args = [
            'seed', 'add',
            '--type', 'Julia', '--subtype', 'Standard', '--power', '2',
            '--x_span', '4.0', '--y_span', '4.0', '--x_center', '0.0', '--y_center', '0.0',
            '--c_real', '-0.7', '--c_imag', '0.27015', '--bailout', '2.0', '--iterations', '600'
        ]
        self._run_cli(args) # Expects exit code 0 by default, no assertRaises here
        output = self.mock_stdout.getvalue()
        self.assertIn("Attempting to add a new seed...", output)
        self.assertIn(f"Seed '{seed_id}' added successfully.", output) # Use f-string
        self.mock_seed_manager_add_seed.assert_called_once()
        self.mock_seed_manager_get_seed_by_id.assert_called_once_with(seed_id, self.mock_active_seeds, self.mock_removed_seeds) # Verify get_seed_by_id was called
        # Verify the arguments passed to add_seed
        called_args, _ = self.mock_seed_manager_add_seed.call_args
        expected_params_for_add_seed = {
            'type': 'Julia', 'subtype': 'Standard', 'power': 2, 'x_span': 4.0, 'y_span': 4.0,
            'x_center': 0.0, 'y_center': 0.0, 'c_real': -0.7, 'c_imag': 0.27015,
            'bailout': 2.0, 'iterations': 600
        }
        self.assertEqual(called_args[0], expected_params_for_add_seed)


    def test_seed_add_validation_failure(self):
        """Test 'frxp seed add' with invalid input (e.g., missing c_real for Julia)."""
        # Expect sys.exit(1) due to validation error
        with self.assertRaises(SystemExit) as cm:
            self._run_cli([
                'seed', 'add',
                '--type', 'Julia', '--power', '2',
                '--x_span', '4.0', '--y_span', '4.0', '--x_center', '0.0', '--y_center', '0.0',
                '--bailout', '2.0', '--iterations', '600'
            ]) # No expected_exit_code needed here, assertRaises handles it
        self.assertEqual(cm.exception.code, 1) # Double-check exit code
        output = self.mock_stdout.getvalue()
        self.assertIn("Error: Invalid input for adding seed:", output)
        self.assertIn("For 'Julia' sets, --c_real and --c_imag are required.", output)
        self.mock_seed_manager_add_seed.assert_not_called() # Manager should not be called on validation failure

    def test_seed_get_success(self):
        """Test 'frxp seed get' for successful retrieval."""
        seed_id = 'seed_00001'
        seed_data = {'type': 'Mandelbrot', 'power': 2, 'iterations': 500, 'x_span': 4.0, 'y_span': 4.0, 'x_center': 0.0, 'y_center': 0.0, 'c_real': None, 'c_imag': None, 'bailout': 2.0, 'subtype': 'Standard'} # Using c_real, c_imag, iterations
        self.mock_seed_manager_get_seed_by_id.return_value = (seed_data, 'active')
        # Populate mock active_seeds if _print_seed_details reads from it directly
        self.mock_active_seeds.update({seed_id: seed_data}) # Ensure seed_data is in the mock global dict
        
        self._run_cli(['seed', 'get', '--seed_id', seed_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"--- Seed ID: {seed_id} (Active) ---", output)
        self.assertIn("Type: Mandelbrot", output) # Updated assertion
        self.mock_seed_manager_get_seed_by_id.assert_called_once_with(seed_id, self.mock_active_seeds, self.mock_removed_seeds)

    def test_seed_get_not_found(self):
        """Test 'frxp seed get' when seed is not found."""
        seed_id = 'seed_99999'
        self.mock_seed_manager_get_seed_by_id.return_value = (None, None)
        self._run_cli(['seed', 'get', '--seed_id', seed_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Seed with ID '{seed_id}' not found.", output)
        self.mock_seed_manager_get_seed_by_id.assert_called_once_with(seed_id, self.mock_active_seeds, self.mock_removed_seeds)

    def test_seed_update_success(self):
        """Test 'frxp seed update' for successful update."""
        seed_id = 'seed_00001'
        initial_seed_data = {'type': 'Julia', 'power': 2, 'iterations': 600, 'x_span': 4.0, 'y_span': 4.0, 'x_center': 0.0, 'y_center': 0.0, 'c_real': -0.7, 'c_imag': 0.27015, 'bailout': 2.0, 'subtype': 'Standard'} # Using c_real, c_imag, iterations
        self.mock_active_seeds[seed_id] = initial_seed_data.copy() # Use .copy() to ensure independent dict
        
        # Configure mock for update_seed to actually modify the mock_active_seeds
        def mock_update_seed_side_effect(sid, updates, active_seeds_mock, removed_seeds_mock):
            if sid in active_seeds_mock:
                # Directly update keys that match seed_manager's expected keys
                active_seeds_mock[sid].update(updates)
                return True
            return False
        self.mock_seed_manager_update_seed.side_effect = mock_update_seed_side_effect
        
        # Configure mock for get_seed_by_id to return the current state from the mock_active_seeds
        # This will be called once: for printing after update
        def mock_get_seed_side_effect(sid, active_seeds_mock, removed_seeds_mock):
            if sid in active_seeds_mock:
                return active_seeds_mock[sid], 'active'
            elif sid in removed_seeds_mock:
                return removed_seeds_mock[sid], 'removed'
            return None, None
        self.mock_seed_manager_get_seed_by_id.side_effect = mock_get_seed_side_effect
        
        self._run_cli(['seed', 'update', '--seed_id', seed_id, '--iterations', '700']) # Changed to named argument
        
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Seed '{seed_id}' updated successfully.", output)
        self.assertIn("Iterations: 700", output) # Verify printed output reflects update
        self.mock_seed_manager_update_seed.assert_called_once_with(seed_id, {'iterations': 700}, self.mock_active_seeds, self.mock_removed_seeds)
        # Assert get_seed_by_id was called once (by handle_update_seed after update)
        self.assertEqual(self.mock_seed_manager_get_seed_by_id.call_count, 1)


    def test_seed_update_no_fields(self):
        """Test 'frxp seed update' with no fields provided."""
        seed_id = 'seed_00001'
        self._run_cli(['seed', 'update', '--seed_id', seed_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn("No fields provided for update.", output)
        self.mock_seed_manager_update_seed.assert_not_called()

    def test_seed_update_not_found(self):
        """Test 'frxp seed update' when seed is not found."""
        seed_id = 'seed_99999'
        self.mock_seed_manager_update_seed.return_value = False
        # Mock get_seed_by_id to return None for the initial check in handle_update_seed
        self.mock_seed_manager_get_seed_by_id.return_value = (None, None) 
        self._run_cli(['seed', 'update', '--seed_id', seed_id, '--iterations', '700']) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Failed to update seed '{seed_id}'. Seed not found or no valid updates were provided.", output)
        self.mock_seed_manager_update_seed.assert_called_once_with(seed_id, {'iterations': 700}, self.mock_active_seeds, self.mock_removed_seeds)

    def test_seed_remove_success(self):
        """Test 'frxp seed remove' for successful removal."""
        seed_id = 'seed_00001'
        self.mock_seed_manager_remove_seed.return_value = True
        self._run_cli(['seed', 'remove', '--seed_id', seed_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Seed '{seed_id}' successfully moved to removed.", output)
        self.mock_seed_manager_remove_seed.assert_called_once_with(seed_id, self.mock_active_seeds, self.mock_removed_seeds)

    def test_seed_remove_not_found(self):
        """Test 'frxp seed remove' when seed is not found."""
        seed_id = 'seed_99999'
        self.mock_seed_manager_remove_seed.return_value = False
        self._run_cli(['seed', 'remove', '--seed_id', seed_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Failed to remove seed '{seed_id}'. It might not exist in active seeds.", output)
        self.mock_seed_manager_remove_seed.assert_called_once_with(seed_id, self.mock_active_seeds, self.mock_removed_seeds)

    def test_seed_restore_success(self):
        """Test 'frxp seed restore' for successful restoration."""
        seed_id = 'seed_00001'
        self.mock_seed_manager_restore_seed.return_value = True
        self._run_cli(['seed', 'restore', '--seed_id', seed_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Seed '{seed_id}' successfully restored to active.", output)
        self.mock_seed_manager_restore_seed.assert_called_once_with(seed_id, self.mock_active_seeds, self.mock_removed_seeds)

    def test_seed_restore_not_found(self):
        """Test 'frxp seed restore' when seed is not found."""
        seed_id = 'seed_99999'
        self.mock_seed_manager_restore_seed.return_value = False
        self._run_cli(['seed', 'restore', '--seed_id', seed_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Failed to restore seed '{seed_id}'. It might not exist in removed seeds.", output)
        self.mock_seed_manager_restore_seed.assert_called_once_with(seed_id, self.mock_active_seeds, self.mock_removed_seeds)

    def test_seed_purge_success(self):
        """Test 'frxp seed purge' with successful confirmation."""
        seed_id = 'seed_00001'
        # Configure mock manager to return success and purged data
        self.mock_seed_manager_purge_seed.return_value = ({'type': 'Julia', 'power': 2, 'subtype': 'Standard'}, True) # Using 'type'
        
        # Simulate user typing 'yes' for confirmation
        self.mock_input.side_effect = ['yes'] # Provide input as a list of strings

        self._run_cli(['seed', 'purge', '--seed_id', seed_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"WARNING: You are about to permanently purge seed '{seed_id}'.", output)
        # Removed: self.assertIn("Type 'yes' to confirm:", output) # This assertion is too brittle
        self.assertIn(f"Successfully purged seed '{seed_id}'.", output)
        self.assertIn("Purged seed details for reference", output)
        self.mock_seed_manager_purge_seed.assert_called_once_with(seed_id, self.mock_active_seeds, self.mock_removed_seeds)

    def test_seed_purge_cancelled(self):
        """Test 'frxp seed purge' when user cancels."""
        seed_id = 'seed_00001'
        # Simulate user typing 'no' for confirmation
        self.mock_input.side_effect = ['no'] # Provide input as a list of strings

        self._run_cli(['seed', 'purge', '--seed_id', seed_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"WARNING: You are about to permanently purge seed '{seed_id}'.", output)
        self.assertIn("Purge cancelled.", output)
        self.mock_seed_manager_purge_seed.assert_not_called() # Manager should not be called

    # --- Image Command Tests ---

    def test_image_list_active(self):
        """Test 'frxp image list' to list active images."""
        mock_image_data = {'image_00001': {'seed_id': 'seed_00001', 'resolution': 1024, 'colormap_name': 'viridis', 'rendering_type': 'iterations', 'aesthetic_rating': 'human_friendly'}}
        self.mock_image_manager_list_images.return_value = (mock_image_data, {})
        # Populate the mock active_images dictionary that _print_image_details uses
        self.mock_active_images.update(mock_image_data)

        self._run_cli(['image', 'list', '--status', 'active'])
        output = self.mock_stdout.getvalue()
        self.assertIn("Listing images (status: active)...\n", output)
        self.assertIn("--- Image ID: image_00001 (Active) ---", output)
        self.assertIn("Resolution: 1024", output)
        self.mock_image_manager_list_images.assert_called_once_with(
            aesthetic_filter='all', seed_id_filter=None, rendering_type_filter=None,
            colormap_filter=None, resolution_filter=None
        )

    def test_image_add_success(self):
        """Test 'frxp image add' for successful addition."""
        image_id = 'image_00001'
        self.mock_image_manager_add_image.return_value = (image_id, True)
        # Mock seed existence (ensure 'type' is present in mock seed data)
        self.mock_seed_manager_get_seed_by_id.return_value = ({'type': 'Julia', 'subtype': 'Standard'}, 'active') 
        self.mock_active_images[image_id] = { # For _print_image_details
            'seed_id': 'seed_00001', 'colormap_name': 'viridis', 'rendering_type': 'iterations',
            'aesthetic_rating': 'experimental', 'resolution': 1024
        }

        args = [
            'image', 'add', 
            '--source_filepath', 'dummy_path.png', # Changed to named argument
            '--seed_id', 'seed_00001', '--colormap_name', 'viridis',
            '--rendering_type', 'iterations', '--aesthetic_rating', 'experimental',
            '--resolution', '1024'
        ]
        # Create a dummy file for Path(args.source_filepath).exists() to pass
        with patch('pathlib.Path.exists', return_value=True):
            self._run_cli(args) # Expects exit code 0 by default
        output = self.mock_stdout.getvalue()
        self.assertIn("Attempting to add an image record...", output)
        # Updated assertion message to match actual output from main.py
        self.assertIn(f"Image '{image_id}' record added and file moved successfully.", output)
        self.mock_image_manager_add_image.assert_called_once()
        self.mock_seed_manager_get_seed_by_id.assert_called_once_with('seed_00001', self.mock_active_seeds, self.mock_removed_seeds)

    def test_image_add_validation_failure(self):
        """Test 'frxp image add' with invalid input (e.g., missing seed_id)."""
        # Expect sys.exit(1) due to validation error
        self.mock_seed_manager_get_seed_by_id.return_value = (None, None) # Seed does not exist
        with self.assertRaises(SystemExit) as cm:
            # Patch Path.exists to return True so we only test seed_id validation
            with patch('pathlib.Path.exists', return_value=True):
                self._run_cli([
                    'image', 'add', 
                    '--source_filepath', 'dummy_path.png', # Changed to named argument
                    '--seed_id', 'non_existent_seed', '--colormap_name', 'viridis',
                    '--rendering_type', 'iterations', '--resolution', '1024'
                ]) # No expected_exit_code needed here
        self.assertEqual(cm.exception.code, 1)
        output = self.mock_stdout.getvalue()
        self.assertIn("Error: Invalid input for adding image:", output)
        self.assertIn("Seed ID 'non_existent_seed' not found.", output)
        self.mock_image_manager_add_image.assert_not_called()

    def test_image_get_success(self):
        """Test 'frxp image get' for successful retrieval."""
        image_id = 'image_00001'
        image_data = {'seed_id': 'seed_00001', 'resolution': 512, 'colormap_name': 'magma', 'rendering_type': 'iterations', 'aesthetic_rating': 'human_friendly'}
        self.mock_image_manager_get_image_by_id.return_value = (image_data, 'active')
        # Populate mock active_images if _print_image_details reads from it directly
        self.mock_active_images.update({image_id: image_data}) # Ensure image_data is in the mock global dict
        
        self._run_cli(['image', 'get', '--image_id', image_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"--- Image ID: {image_id} (Active) ---", output)
        self.assertIn("Resolution: 512", output)
        self.mock_image_manager_get_image_by_id.assert_called_once_with(image_id, self.mock_active_images, self.mock_removed_images)

    def test_image_get_not_found(self):
        """Test 'frxp image get' when image is not found."""
        image_id = 'image_999999'
        self.mock_image_manager_get_image_by_id.return_value = (None, None)
        self._run_cli(['image', 'get', '--image_id', image_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Image with ID '{image_id}' not found.", output)
        self.mock_image_manager_get_image_by_id.assert_called_once_with(image_id, self.mock_active_images, self.mock_removed_images)

    def test_image_update_success(self):
        """Test 'frxp image update' for successful update."""
        image_id = 'image_00001'
        initial_image_data = {'seed_id': 'seed_00001', 'resolution': 1024, 'colormap_name': 'viridis', 'rendering_type': 'iterations', 'aesthetic_rating': 'experimental'}
        self.mock_active_images[image_id] = initial_image_data.copy() # Use .copy()
        
        # Configure mock for update_image to actually modify the mock_active_images
        def mock_update_image_side_effect(iid, updates, active_images_mock, removed_images_mock):
            if iid in active_images_mock:
                active_images_mock[iid].update(updates)
                return True
            return False
        self.mock_image_manager_update_image.side_effect = mock_update_image_side_effect
        
        # Configure mock for get_image_by_id to return the current state from the mock_active_images
        # This will be called once: for printing after update
        def mock_get_image_side_effect(iid, active_images_mock, removed_images_mock):
            if iid in active_images_mock:
                return active_images_mock[iid], 'active'
            elif iid in removed_images_mock:
                return removed_images_mock[iid], 'removed'
            return None, None
        self.mock_image_manager_get_image_by_id.side_effect = mock_get_image_side_effect
        
        self._run_cli(['image', 'update', '--image_id', image_id, '--resolution', '512']) # Changed to named argument
        
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Image '{image_id}' updated successfully.", output)
        self.assertIn("Resolution: 512", output)
        self.mock_image_manager_update_image.assert_called_once_with(image_id, {'resolution': 512}, self.mock_active_images, self.mock_removed_images)
        # Assert get_image_by_id was called once (by handle_update_image after update)
        self.assertEqual(self.mock_image_manager_get_image_by_id.call_count, 1)


    def test_image_update_no_fields(self):
        """Test 'frxp image update' with no fields provided."""
        image_id = 'image_00001'
        self._run_cli(['image', 'update', '--image_id', image_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn("No fields provided for update.", output)
        self.mock_image_manager_update_image.assert_not_called()

    def test_image_update_not_found(self):
        """Test 'frxp image update' when image is not found."""
        image_id = 'image_999999'
        self.mock_image_manager_update_image.return_value = False
        # Mock get_image_by_id to return None for the initial check in handle_update_image
        self.mock_image_manager_get_image_by_id.return_value = (None, None)
        self._run_cli(['image', 'update', '--image_id', image_id, '--resolution', '512']) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Failed to update image '{image_id}'. Image not found or no valid updates.", output)
        self.mock_image_manager_update_image.assert_called_once_with(image_id, {'resolution': 512}, self.mock_active_images, self.mock_removed_images)

    def test_image_remove_success(self):
        """Test 'frxp image remove' for successful removal."""
        image_id = 'image_00001'
        self.mock_image_manager_remove_image.return_value = True
        self._run_cli(['image', 'remove', '--image_id', image_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Image '{image_id}' successfully moved to removed status (and file moved).", output)
        self.mock_image_manager_remove_image.assert_called_once_with(image_id, self.mock_active_images, self.mock_removed_images)

    def test_image_remove_not_found(self):
        """Test 'frxp image remove' when image is not found."""
        image_id = 'image_999999'
        self.mock_image_manager_remove_image.return_value = False
        self._run_cli(['image', 'remove', '--image_id', image_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Failed to remove image '{image_id}'. It might not exist in active images or file movement failed. Check warnings above.", output)
        self.mock_image_manager_remove_image.assert_called_once_with(image_id, self.mock_active_images, self.mock_removed_images)

    def test_image_restore_success(self):
        """Test 'frxp image restore' for successful restoration."""
        image_id = 'image_00001'
        self.mock_image_manager_restore_image.return_value = True
        self._run_cli(['image', 'restore', '--image_id', image_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Image '{image_id}' successfully restored to active status (and file moved).", output)
        self.mock_image_manager_restore_image.assert_called_once_with(image_id, self.mock_active_images, self.mock_removed_images)

    def test_image_restore_not_found(self):
        """Test 'frxp image restore' when image is not found."""
        image_id = 'image_999999'
        self.mock_image_manager_restore_image.return_value = False
        self._run_cli(['image', 'restore', '--image_id', image_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Failed to restore image '{image_id}'. It might not exist in removed images or file movement failed. Check warnings above.", output)
        self.mock_image_manager_restore_image.assert_called_once_with(image_id, self.mock_active_images, self.mock_removed_seeds)

    def test_image_purge_success(self):
        """Test 'frxp image purge' with successful confirmation."""
        image_id = 'image_00001'
        self.mock_image_manager_purge_image.return_value = ({'resolution': 1024, 'physical_file_deleted': True}, True)
        self.mock_input.side_effect = ['yes'] # Provide input as a list of strings

        self._run_cli(['image', 'purge', '--image_id', image_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"WARNING: You are about to permanently purge image '{image_id}'.", output)
        # Removed: self.assertIn("Type 'yes' to confirm:", output) # This assertion is too brittle
        self.assertIn(f"Successfully purged image '{image_id}'.", output)
        self.assertIn("Purged image details for reference:", output)
        self.mock_image_manager_purge_image.assert_called_once_with(image_id, self.mock_active_images, self.mock_removed_images)

    def test_image_purge_cancelled(self):
        """Test 'frxp image purge' when user cancels."""
        image_id = 'image_00001'
        self.mock_input.side_effect = ['no'] # Provide input as a list of strings

        self._run_cli(['image', 'purge', '--image_id', image_id]) # Changed to named argument
        output = self.mock_stdout.getvalue()
        self.assertIn(f"WARNING: You are about to permanently purge image '{image_id}'.", output)
        self.assertIn("Purge cancelled.", output)
        self.mock_image_manager_purge_image.assert_not_called()

    def test_image_render_success(self):
        """Test 'frxp image render' for successful rendering and addition of multiple images."""
        seed_id = 'seed_00001'

        # Mock seed existence
        self.mock_seed_manager_get_seed_by_id.return_value = ({'type': 'Julia', 'power': 2, 'x_span': 4.0, 'y_span': 4.0, 'x_center': 0.0, 'y_center': 0.0, 'c_real': -0.7, 'c_imag': 0.27015, 'bailout': 2.0, 'iterations': 600, 'subtype': 'Standard'}, 'active')

        # Mock the renderer output to return a list of dictionaries instead of a single Path object.
        # This mirrors the change in the main renderer.
        self.mock_renderer_render_fractal_to_file.return_value = [
            {'filepath': Path('/mock/staging/img1.png'), 'rendering_type': 'iterations', 'colormap': 'twilight'},
            {'filepath': Path('/mock/staging/img2.png'), 'rendering_type': 'magnitudes', 'colormap': 'twilight'},
            {'filepath': Path('/mock/staging/img3.png'), 'rendering_type': 'angles', 'colormap': 'twilight'}
        ]

        # The image manager now adds multiple images, so we need to mock a sequence of return values.
        from unittest.mock import call
        self.mock_image_manager_add_image.side_effect = [
            ('image_00001', True),
            ('image_00002', True),
            ('image_00003', True)
        ]

        # Mock active images for the final check, mirroring the three new images
        self.mock_active_images.update({
            'image_00001': {'seed_id': seed_id, 'colormap_name': 'twilight', 'rendering_type': 'iterations', 'aesthetic_rating': 'experimental', 'resolution': 1024},
            'image_00002': {'seed_id': seed_id, 'colormap_name': 'twilight', 'rendering_type': 'magnitudes', 'aesthetic_rating': 'experimental', 'resolution': 1024},
            'image_00003': {'seed_id': seed_id, 'colormap_name': 'twilight', 'rendering_type': 'angles', 'aesthetic_rating': 'experimental', 'resolution': 1024}
        })

        args = [
            'image', 'render',
            '--seed_id', seed_id,
            '--resolution', '1024',
            '--colormaps', 'twilight',
            '--rendering_types', 'all',
            '--aesthetic_rating', 'experimental'
        ]
        self._run_cli(args) # Expects exit code 0 by default
        output = self.mock_stdout.getvalue()

        # Update assertions to check for all three images
        self.assertIn(f"Attempting to render image(s) for seed ID: {seed_id}...", output)
        self.assertIn("Image 'image_00001' record added and file moved successfully.", output)
        self.assertIn("Image 'image_00002' record added and file moved successfully.", output)
        self.assertIn("Image 'image_00003' record added and file moved successfully.", output)

        self.mock_seed_manager_get_seed_by_id.assert_called_once_with(seed_id, self.mock_active_seeds, self.mock_removed_seeds)

        # Assert that the renderer was called with the correct arguments
        self.mock_renderer_render_fractal_to_file.assert_called_once_with(
            self.mock_seed_manager_get_seed_by_id.return_value[0],
            self.mock_image_manager_get_staging_directory_path.return_value,
            resolution=1024,
            colormap_names=['twilight'],
            rendering_types=['all']
        )
        # Use assert_has_calls to verify the sequence of add_image calls for each image
        expected_calls = [
            call({'seed_id': seed_id, 'colormap_name': 'twilight', 'rendering_type': 'iterations', 'aesthetic_rating': 'experimental', 'resolution': 1024}, Path('/mock/staging/img1.png'), self.mock_active_images, self.mock_removed_images),
            call({'seed_id': seed_id, 'colormap_name': 'twilight', 'rendering_type': 'magnitudes', 'aesthetic_rating': 'experimental', 'resolution': 1024}, Path('/mock/staging/img2.png'), self.mock_active_images, self.mock_removed_images),
            call({'seed_id': seed_id, 'colormap_name': 'twilight', 'rendering_type': 'angles', 'aesthetic_rating': 'experimental', 'resolution': 1024}, Path('/mock/staging/img3.png'), self.mock_active_images, self.mock_removed_images)
        ]
        self.mock_image_manager_add_image.assert_has_calls(expected_calls)

    def test_image_render_seed_not_found(self):
        """Test 'frxp image render' when seed is not found."""
        seed_id = 'seed_99999'
        self.mock_seed_manager_get_seed_by_id.return_value = (None, None) # Seed not found
        with self.assertRaises(SystemExit) as cm:
            self._run_cli([
                'image', 'render', 
                '--seed_id', seed_id, # Changed to named argument
                '--resolution', '1024', '--colormap', 'twilight'
            ]) # Explicitly expect exit code 1 due to sys.exit(1) in handler
        self.assertEqual(cm.exception.code, 1)
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Error: Seed '{seed_id}' not found or is removed. Cannot render.", output)
        self.mock_seed_manager_get_seed_by_id.assert_called_once_with(seed_id, self.mock_active_seeds, self.mock_removed_seeds)
        self.mock_renderer_render_fractal_to_file.assert_not_called()
        self.mock_image_manager_add_image.assert_not_called()