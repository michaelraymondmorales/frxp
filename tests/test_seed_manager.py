import os
import unittest
from pathlib import Path
from fractal_explorer_vae.core.data_managers import seed_manager

class TestSeedManager(unittest.TestCase):

    def setUp(self):
        """
        Set up a temporary environment for each test.
        This ensures tests are isolated and don't interfere with real data.
        """
        self.test_dir = Path("test_data_seed_manager")
        self.test_dir.mkdir(exist_ok=True)

        # Override manager's file paths to point to temporary files
        self.original_active_seeds_file = seed_manager.ACTIVE_SEEDS_FILE
        self.original_removed_seeds_file = seed_manager.REMOVED_SEEDS_FILE

        seed_manager.ACTIVE_SEEDS_FILE = self.test_dir / "test_active_fractal_seeds.json"
        seed_manager.REMOVED_SEEDS_FILE = self.test_dir / "test_removed_fractal_seeds.json"

        # Ensure test files are empty at the start of each test
        if seed_manager.ACTIVE_SEEDS_FILE.exists():
            os.remove(seed_manager.ACTIVE_SEEDS_FILE)
        if seed_manager.REMOVED_SEEDS_FILE.exists():
            os.remove(seed_manager.REMOVED_SEEDS_FILE)

        # Initialize empty data for tests
        self.active_seeds = {}
        self.removed_seeds = {}

        # Define a sample seed for testing
        self.sample_seed_params = {
            'type': 'Julia',
            'subtype': 'Multi-Julia',
            'power': 2,
            'x_span': 4.0,
            'y_span': 4.0,
            'x_center': 0.0,
            'y_center': 0.0,
            'c_real': -0.7,
            'c_imag': 0.27015,
            'bailout': 2.0,
            'iterations': 600
        }

    def tearDown(self):
        """
        Clean up the temporary environment after each test.
        """
        # Remove temporary files
        if seed_manager.ACTIVE_SEEDS_FILE.exists():
            os.remove(seed_manager.ACTIVE_SEEDS_FILE)
        if seed_manager.REMOVED_SEEDS_FILE.exists():
            os.remove(seed_manager.REMOVED_SEEDS_FILE)
        
        # Remove temporary directory
        if self.test_dir.exists():
            self.test_dir.rmdir() # rmdir only works if directory is empty

        # Restore original file paths to avoid affecting other tests or main app
        seed_manager.ACTIVE_SEEDS_FILE = self.original_active_seeds_file
        seed_manager.REMOVED_SEEDS_FILE = self.original_removed_seeds_file

    # --- Test Cases ---

    def test_add_seed(self):
        # Test adding a single seed
        seed_id = seed_manager.add_seed(self.sample_seed_params, self.active_seeds, self.removed_seeds)
        self.assertIsNotNone(seed_id)
        self.assertTrue(seed_id.startswith('seed_'))
        self.assertEqual(len(self.active_seeds), 1)
        self.assertEqual(self.active_seeds[seed_id]['type'], 'Julia')
        
        # Test that data is saved to file
        loaded_active, loaded_removed = seed_manager.load_all_seeds()
        self.assertEqual(loaded_active[seed_id]['power'], 2)
        self.assertEqual(loaded_active[seed_id]['c_real'], -0.7)
        self.assertEqual(loaded_active[seed_id]['c_imag'], 0.27015)


    def test_get_next_seed_id(self):
        # Test ID generation from empty
        self.assertEqual(seed_manager.get_next_seed_id({}, {}), 'seed_00001')
        
        # Add a seed and test next ID
        seed_manager.add_seed(self.sample_seed_params, self.active_seeds, self.removed_seeds)
        self.assertEqual(seed_manager.get_next_seed_id(self.active_seeds, self.removed_seeds), 'seed_00002')

        # Add to removed and test next ID
        seed_manager.remove_seed('seed_00001', self.active_seeds, self.removed_seeds) # Remove the first one
        seed_manager.add_seed(self.sample_seed_params, self.active_seeds, self.removed_seeds) # Add a new one
        self.assertEqual(seed_manager.get_next_seed_id(self.active_seeds, self.removed_seeds), 'seed_00003')

    def test_get_seed_by_id(self):
        seed_id = seed_manager.add_seed(self.sample_seed_params, self.active_seeds, self.removed_seeds)
        
        # Test retrieving active seed
        retrieved_seed, status = seed_manager.get_seed_by_id(seed_id, self.active_seeds, self.removed_seeds)
        self.assertIsNotNone(retrieved_seed)
        self.assertEqual(status, 'active')
        self.assertEqual(retrieved_seed['type'], 'Julia')

        # Test retrieving non-existent seed
        non_existent_seed, status = seed_manager.get_seed_by_id('seed_99999', self.active_seeds, self.removed_seeds)
        self.assertIsNone(non_existent_seed)
        self.assertIsNone(status)

        # Test retrieving removed seed
        seed_manager.remove_seed(seed_id, self.active_seeds, self.removed_seeds)
        retrieved_seed, status = seed_manager.get_seed_by_id(seed_id, self.active_seeds, self.removed_seeds)
        self.assertIsNotNone(retrieved_seed)
        self.assertEqual(status, 'removed')
        self.assertEqual(retrieved_seed['type'], 'Julia')


    def test_update_seed(self):
        seed_id = seed_manager.add_seed(self.sample_seed_params, self.active_seeds, self.removed_seeds)
        
        # Test updating an existing field
        updates = {'iterations': 700, 'x_span': 5.0}
        success = seed_manager.update_seed(seed_id, updates, self.active_seeds, self.removed_seeds)
        self.assertTrue(success)
        self.assertEqual(self.active_seeds[seed_id]['iterations'], 700)
        self.assertEqual(self.active_seeds[seed_id]['x_span'], 5.0)

        # Test updating a non-existent field (should print warning but return True if other updates succeed)
        updates_with_bad_key = {'new_key': 'value', 'power': 3}
        success = seed_manager.update_seed(seed_id, updates_with_bad_key, self.active_seeds, self.removed_seeds)
        self.assertTrue(success) # Still true because power was updated
        self.assertEqual(self.active_seeds[seed_id]['power'], 3)
        self.assertNotIn('new_key', self.active_seeds[seed_id])

        # Test updating non-existent seed
        success = seed_manager.update_seed('seed_99999', {'iterations': 100}, self.active_seeds, self.removed_seeds)
        self.assertFalse(success)

        # Test that updates are persisted
        loaded_active, _ = seed_manager.load_all_seeds()
        self.assertEqual(loaded_active[seed_id]['iterations'], 700)
        self.assertEqual(loaded_active[seed_id]['power'], 3)


    def test_remove_seed(self):
        seed_id = seed_manager.add_seed(self.sample_seed_params, self.active_seeds, self.removed_seeds)
        
        # Test removing an existing seed
        success = seed_manager.remove_seed(seed_id, self.active_seeds, self.removed_seeds)
        self.assertTrue(success)
        self.assertNotIn(seed_id, self.active_seeds)
        self.assertIn(seed_id, self.removed_seeds)

        # Test removing non-existent seed
        success = seed_manager.remove_seed('seed_99999', self.active_seeds, self.removed_seeds)
        self.assertFalse(success)

        # Test that removal is persisted
        loaded_active, loaded_removed = seed_manager.load_all_seeds()
        self.assertNotIn(seed_id, loaded_active)
        self.assertIn(seed_id, loaded_removed)

    def test_restore_seed(self):
        seed_id = seed_manager.add_seed(self.sample_seed_params, self.active_seeds, self.removed_seeds)
        seed_manager.remove_seed(seed_id, self.active_seeds, self.removed_seeds) # First remove it

        # Test restoring a removed seed
        success = seed_manager.restore_seed(seed_id, self.active_seeds, self.removed_seeds)
        self.assertTrue(success)
        self.assertIn(seed_id, self.active_seeds)
        self.assertNotIn(seed_id, self.removed_seeds)

        # Test restoring non-existent seed (not in removed)
        success = seed_manager.restore_seed('seed_99999', self.active_seeds, self.removed_seeds)
        self.assertFalse(success)

        # Test that restoration is persisted
        loaded_active, loaded_removed = seed_manager.load_all_seeds()
        self.assertIn(seed_id, loaded_active)
        self.assertNotIn(seed_id, loaded_removed)

    def test_list_seeds(self):
        seed1_id = seed_manager.add_seed(self.sample_seed_params, self.active_seeds, self.removed_seeds)
        seed2_params = self.sample_seed_params.copy()
        seed2_params['type'] = 'Mandelbrot'
        seed2_id = seed_manager.add_seed(seed2_params, self.active_seeds, self.removed_seeds)
        
        # Test listing active seeds
        active_seeds = seed_manager.list_seeds(self.active_seeds, self.removed_seeds, 'active')
        self.assertEqual(len(active_seeds), 2)
        self.assertIn(seed1_id, active_seeds)
        self.assertIn(seed2_id, active_seeds)

        # Move one to removed
        seed_manager.remove_seed(seed1_id, self.active_seeds, self.removed_seeds)

        # Test listing active seeds after removal
        active_seeds = seed_manager.list_seeds(self.active_seeds, self.removed_seeds, 'active')
        self.assertEqual(len(active_seeds), 1)
        self.assertIn(seed2_id, active_seeds)
        self.assertNotIn(seed1_id, active_seeds)

        # Test listing removed seeds
        removed_seeds = seed_manager.list_seeds(self.active_seeds, self.removed_seeds, 'removed')
        self.assertEqual(len(removed_seeds), 1)
        self.assertIn(seed1_id, removed_seeds)
        self.assertNotIn(seed2_id, removed_seeds)

        # Test listing all seeds
        all_seeds = seed_manager.list_seeds(self.active_seeds, self.removed_seeds, 'all')
        self.assertEqual(len(all_seeds), 2)
        self.assertIn(seed1_id, all_seeds)
        self.assertIn(seed2_id, all_seeds)
        # Check sorting (by ID string)
        self.assertEqual(list(all_seeds.keys()), sorted([seed1_id, seed2_id]))

        # Test invalid status
        invalid_status_seeds = seed_manager.list_seeds(self.active_seeds, self.removed_seeds, 'invalid')
        self.assertEqual(len(invalid_status_seeds), 0)


# To run these tests from the project root:
# python -m unittest tests/test_seed_manager.py