import unittest
import sys
import shutil
from io import StringIO
from pathlib import Path
from unittest.mock import patch

# Import the main CLI entry point function
from frxp.cli.main import main
# Import the actual manager modules to patch their file paths
from frxp.core.data_managers import seed_manager
from frxp.core.data_managers import image_manager

class TestCLIIntegration(unittest.TestCase):

    def setUp(self):
        """
        Set up a temporary environment for each integration test.
        This includes:
        - Creating temporary directories for data files and images.
        - Overriding the data manager's file paths to point to these temporary locations.
        - Mocking sys.stdout to capture CLI output.
        - Mocking sys.stdin for interactive prompts (like purge confirmation).
        """
        # 1. Create temporary root directory for all test data
        self.test_root_dir = Path("temp_integration_test_data")
        self.test_root_dir.mkdir(exist_ok=True)

        # 2. Override manager's file paths to point to temporary files
        # Store original paths to restore them in tearDown
        self.original_seed_active_file = seed_manager.ACTIVE_SEEDS_FILE
        self.original_seed_removed_file = seed_manager.REMOVED_SEEDS_FILE
        self.original_image_active_file = image_manager.ACTIVE_IMAGES_FILE
        self.original_image_removed_file = image_manager.REMOVED_IMAGES_FILE
        self.original_rendered_fractals_dir = image_manager.RENDERED_FRACTALS_DIR
        self.original_active_images_dir = image_manager.ACTIVE_IMAGES_DIR
        self.original_removed_images_dir = image_manager.REMOVED_IMAGES_DIR
        self.original_staging_images_dir = image_manager.STAGING_IMAGES_DIR

        # Set new temporary paths for the managers
        seed_manager.ACTIVE_SEEDS_FILE = self.test_root_dir / "test_active_fractal_seeds.json"
        seed_manager.REMOVED_SEEDS_FILE = self.test_root_dir / "test_removed_fractal_seeds.json"
        image_manager.ACTIVE_IMAGES_FILE = self.test_root_dir / "test_active_fractal_images.json"
        image_manager.REMOVED_IMAGES_FILE = self.test_root_dir / "test_removed_fractal_images.json"
        
        # Create temporary image directories within the test root
        self.test_rendered_fractals_dir = self.test_root_dir / "rendered_fractals"
        self.test_active_images_dir = self.test_rendered_fractals_dir / "active"
        self.test_removed_images_dir = self.test_rendered_fractals_dir / "removed"
        self.test_staging_images_dir = self.test_rendered_fractals_dir / "staging"

        self.test_active_images_dir.mkdir(parents=True, exist_ok=True)
        self.test_removed_images_dir.mkdir(parents=True, exist_ok=True)
        self.test_staging_images_dir.mkdir(parents=True, exist_ok=True)

        image_manager.RENDERED_FRACTALS_DIR = self.test_rendered_fractals_dir
        image_manager.ACTIVE_IMAGES_DIR = self.test_active_images_dir
        image_manager.REMOVED_IMAGES_DIR = self.test_removed_images_dir
        image_manager.STAGING_IMAGES_DIR = self.test_staging_images_dir

        # Ensure test files are empty at the start of each test
        for f in [seed_manager.ACTIVE_SEEDS_FILE, seed_manager.REMOVED_SEEDS_FILE,
                  image_manager.ACTIVE_IMAGES_FILE, image_manager.REMOVED_IMAGES_FILE]:
            if f.exists():
                f.unlink() # Delete the file

        # 3. Mock sys.stdout to capture print statements
        self.held_stdout = sys.stdout
        self.mock_stdout = StringIO()
        sys.stdout = self.mock_stdout

        # 4. Mock sys.stdin for `input()` calls
        self.input_patcher = patch('builtins.input')
        self.mock_input = self.input_patcher.start()

        # 5. Reset sys.argv for each test
        self.original_argv = sys.argv
        sys.argv = ['main.py'] # Default to just the script name

        # 6. Patch the renderer's actual rendering function to avoid long computations
        # For integration tests, we want to test the CLI's interaction with managers,
        # not the rendering algorithm itself. We just need it to produce a dummy file.
        self.mock_renderer_render_fractal_to_file = patch(
            'frxp.cli.renderer.render_fractal_to_file'
        ).start()
        # Make the mock renderer create a dummy file in the specified staging directory
        def dummy_render_side_effect(seed_data, output_dir, resolution, colormap_name):
            dummy_filepath = output_dir / f"dummy_fractal_{resolution}_{colormap_name}.png"
            dummy_filepath.touch() # Create an empty file
            return dummy_filepath
        self.mock_renderer_render_fractal_to_file.side_effect = dummy_render_side_effect


    def tearDown(self):
        """
        Clean up the temporary environment and restore original paths.
        """
        # Stop all patches
        patch.stopall()

        # Restore sys.stdout and sys.stdin
        sys.stdout = self.held_stdout
        sys.stdin = sys.__stdin__

        # Restore sys.argv
        sys.argv = self.original_argv

        # Restore original manager file paths
        seed_manager.ACTIVE_SEEDS_FILE = self.original_seed_active_file
        seed_manager.REMOVED_SEEDS_FILE = self.original_seed_removed_file
        image_manager.ACTIVE_IMAGES_FILE = self.original_image_active_file
        image_manager.REMOVED_IMAGES_FILE = self.original_image_removed_file
        image_manager.RENDERED_FRACTALS_DIR = self.original_rendered_fractals_dir
        image_manager.ACTIVE_IMAGES_DIR = self.original_active_images_dir
        image_manager.REMOVED_IMAGES_DIR = self.original_removed_images_dir
        image_manager.STAGING_IMAGES_DIR = self.original_staging_images_dir

        # Remove the temporary test directory
        if self.test_root_dir.exists():
            shutil.rmtree(self.test_root_dir)

    def _run_cli(self, args_list):
        """
        Helper to run the main CLI function with given arguments.
        Catches SystemExit to allow tests to continue after CLI exits.
        """
        sys.argv = ['main.py'] + args_list
        try:
            main(argv=args_list) # Pass args_list directly to main
        except SystemExit as e:
            # We expect SystemExit for some CLI commands (e.g., --help, validation errors)
            # Store the exit code if needed for assertions, but don't re-raise
            self.cli_exit_code = e.code
        except Exception as e:
            self.fail(f"CLI raised an unexpected exception: {e}")
            self.cli_exit_code = 1 # Indicate an error if an unexpected exception occurs
        else:
            self.cli_exit_code = 0 # Indicate success if no exception

    # --- Integration Tests will go here ---
    # Example:
    # def test_add_seed_and_verify_file(self):
    #     self._run_cli(['seed', 'add', ...])
    #     output = self.mock_stdout.getvalue()
    #     self.assertIn("Seed 'seed_00001' added successfully.", output)
    #     self.assertTrue(seed_manager.ACTIVE_SEEDS_FILE.exists())
    #     # Load and check content of the actual JSON file
    #     loaded_seeds, _ = seed_manager.load_all_seeds()
    #     self.assertIn('seed_00001', loaded_seeds)