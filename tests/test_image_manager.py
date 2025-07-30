import os
import shutil
import unittest
from pathlib import Path
from fractal_explorer_vae.core.data_managers import image_manager

class TestImageManager(unittest.TestCase):

    def setUp(self):
        """
        Set up a temporary environment for each test.
        This includes temporary directories for images and overriding file paths.
        """
        self.test_root_dir = Path("test_data_image_manager")
        self.test_root_dir.mkdir(exist_ok=True)

        # Override manager's file paths to point to temporary files
        self.original_active_images_file = image_manager.ACTIVE_IMAGES_FILE
        self.original_removed_images_file = image_manager.REMOVED_IMAGES_FILE
        self.original_rendered_fractals_dir = image_manager.RENDERED_FRACTALS_DIR
        self.original_active_images_dir = image_manager.ACTIVE_IMAGES_DIR
        self.original_removed_images_dir = image_manager.REMOVED_IMAGES_DIR
        self.original_staging_images_dir = image_manager.STAGING_IMAGES_DIR

        image_manager.ACTIVE_IMAGES_FILE = self.test_root_dir / "test_active_fractal_images.json"
        image_manager.REMOVED_IMAGES_FILE = self.test_root_dir / "test_removed_fractal_images.json"
        
        # Create temporary image directories within the test root
        self.test_rendered_fractals_dir = self.test_root_dir / "rendered_fractals"
        self.test_active_images_dir = self.test_rendered_fractals_dir / "active"
        self.test_removed_images_dir = self.test_rendered_fractals_dir / "removed"
        self.test_staging_images_dir = self.test_rendered_fractals_dir / "staging"

        # Override manager's directory paths
        image_manager.RENDERED_FRACTALS_DIR = self.test_rendered_fractals_dir
        image_manager.ACTIVE_IMAGES_DIR = self.test_active_images_dir
        image_manager.REMOVED_IMAGES_DIR = self.test_removed_images_dir
        image_manager.STAGING_IMAGES_DIR = self.test_staging_images_dir

        # Ensure all test directories exist and are empty
        if self.test_rendered_fractals_dir.exists():
            shutil.rmtree(self.test_rendered_fractals_dir) # Remove recursively
        self.test_active_images_dir.mkdir(parents=True, exist_ok=True)
        self.test_removed_images_dir.mkdir(parents=True, exist_ok=True)
        self.test_staging_images_dir.mkdir(parents=True, exist_ok=True)

        # Ensure test JSON files are empty
        if image_manager.ACTIVE_IMAGES_FILE.exists():
            os.remove(image_manager.ACTIVE_IMAGES_FILE)
        if image_manager.REMOVED_IMAGES_FILE.exists():
            os.remove(image_manager.REMOVED_IMAGES_FILE)

        # Initialize empty data for tests
        self.active_images = {}
        self.removed_images = {}

        # Define a sample image metadata
        self.sample_image_params = {
            'seed_id': 'seed_00001',
            'colormap_name': 'viridis',
            'rendering_type': 'iterations',
            'aesthetic_rating': 'human_friendly',
            'resolution': 1024
        }
        self.dummy_image_content = b"dummy_image_data" # Use bytes for image content

    def tearDown(self):
        """
        Clean up the temporary environment after each test.
        """
        # Remove temporary files and directories
        if self.test_root_dir.exists():
            shutil.rmtree(self.test_root_dir) # Remove recursively

        # Restore original file paths and directory paths
        image_manager.ACTIVE_IMAGES_FILE = self.original_active_images_file
        image_manager.REMOVED_IMAGES_FILE = self.original_removed_images_file
        image_manager.RENDERED_FRACTALS_DIR = self.original_rendered_fractals_dir
        image_manager.ACTIVE_IMAGES_DIR = self.original_active_images_dir
        image_manager.REMOVED_IMAGES_DIR = self.original_removed_images_dir
        image_manager.STAGING_IMAGES_DIR = self.original_staging_images_dir

    # --- Helper to create a dummy image in staging ---
    def _create_dummy_staged_image(self, filename: str = "temp_image.png") -> Path:
        filepath = self.test_staging_images_dir / filename
        with open(filepath, 'wb') as f:
            f.write(self.dummy_image_content)
        return filepath

    # --- Test Cases ---

    def test_add_image_success(self):
        staged_filepath = self._create_dummy_staged_image()
        
        image_id, move_success = image_manager.add_image(
            self.sample_image_params, staged_filepath, self.active_images, self.removed_images
        )
        self.assertTrue(move_success)
        self.assertIsNotNone(image_id)
        self.assertTrue(image_id.startswith('image_'))
        self.assertEqual(len(self.active_images), 1)
        self.assertIn(image_id, self.active_images)
        self.assertEqual(self.active_images[image_id]['seed_id'], 'seed_00001')
        self.assertTrue(self.active_images[image_id]['file_moved_successfully'])

        # Verify physical file moved and staging file is gone
        self.assertFalse(staged_filepath.exists())
        expected_dest_path = self.test_active_images_dir / f"{image_id}{staged_filepath.suffix}"
        self.assertTrue(expected_dest_path.exists())
        with open(expected_dest_path, 'rb') as f:
            self.assertEqual(f.read(), self.dummy_image_content)
        
        # Verify metadata filename path
        self.assertEqual(self.active_images[image_id]['filename'], f'active/{image_id}{staged_filepath.suffix}')

        # Verify data is persisted
        loaded_active, _ = image_manager.load_all_images()
        self.assertIn(image_id, loaded_active)
        self.assertEqual(loaded_active[image_id]['resolution'], 1024)

    def test_add_image_source_not_found(self):
        non_existent_filepath = self.test_staging_images_dir / "non_existent.png"
        
        image_id, move_success = image_manager.add_image(
            self.sample_image_params, non_existent_filepath, self.active_images, self.removed_images
        )
        self.assertFalse(move_success) # Expect move to fail
        self.assertIsNotNone(image_id) # Metadata should still be added
        self.assertIn(image_id, self.active_images)
        self.assertFalse(self.active_images[image_id]['file_moved_successfully']) # Verify flag

        # Verify data is persisted with correct flag
        loaded_active, _ = image_manager.load_all_images()
        self.assertIn(image_id, loaded_active)
        self.assertFalse(loaded_active[image_id]['file_moved_successfully'])


    def test_get_image_by_id(self):
        staged_filepath = self._create_dummy_staged_image()
        image_id, _ = image_manager.add_image(self.sample_image_params, staged_filepath, self.active_images, self.removed_images)
        
        # Test retrieving active image
        retrieved_image, status = image_manager.get_image_by_id(image_id, self.active_images, self.removed_images)
        self.assertIsNotNone(retrieved_image)
        self.assertEqual(status, 'active')
        self.assertEqual(retrieved_image['resolution'], 1024)

        # Test retrieving non-existent image
        non_existent_image, status = image_manager.get_image_by_id('image_999999', self.active_images, self.removed_images)
        self.assertIsNone(non_existent_image)
        self.assertIsNone(status)

        # Test retrieving removed image
        image_manager.remove_image(image_id, self.active_images, self.removed_images)
        retrieved_image, status = image_manager.get_image_by_id(image_id, self.active_images, self.removed_images)
        self.assertIsNotNone(retrieved_image)
        self.assertEqual(status, 'removed')
        self.assertEqual(retrieved_image['resolution'], 1024)

    def test_update_image(self):
        staged_filepath = self._create_dummy_staged_image()
        image_id, _ = image_manager.add_image(self.sample_image_params, staged_filepath, self.active_images, self.removed_images)
        
        # Test updating existing fields
        updates = {'aesthetic_rating': 'data_friendly', 'resolution': 512}
        success = image_manager.update_image(image_id, updates, self.active_images, self.removed_images)
        self.assertTrue(success)
        self.assertEqual(self.active_images[image_id]['aesthetic_rating'], 'data_friendly')
        self.assertEqual(self.active_images[image_id]['resolution'], 512)

        # Test updating non-existent field (should print warning but return True if other updates succeed)
        updates_with_bad_key = {'new_image_key': 'value', 'colormap_name': 'magma'}
        success = image_manager.update_image(image_id, updates_with_bad_key, self.active_images, self.removed_images)
        self.assertTrue(success)
        self.assertEqual(self.active_images[image_id]['colormap_name'], 'magma')
        self.assertNotIn('new_image_key', self.active_images[image_id])

        # Test updating non-existent image
        success = image_manager.update_image('image_999999', {'resolution': 256}, self.active_images, self.removed_images)
        self.assertFalse(success)

        # Test that updates are persisted
        loaded_active, _ = image_manager.load_all_images()
        self.assertEqual(loaded_active[image_id]['aesthetic_rating'], 'data_friendly')
        self.assertEqual(loaded_active[image_id]['colormap_name'], 'magma')


    def test_remove_image_success(self):
        staged_filepath = self._create_dummy_staged_image()
        image_id, _ = image_manager.add_image(self.sample_image_params, staged_filepath, self.active_images, self.removed_images)
        
        # Verify initial state
        active_path = self.test_active_images_dir / f"{image_id}{staged_filepath.suffix}"
        self.assertTrue(active_path.exists())

        # Test removing an existing image
        success = image_manager.remove_image(image_id, self.active_images, self.removed_images)
        self.assertTrue(success)
        self.assertNotIn(image_id, self.active_images)
        self.assertIn(image_id, self.removed_images)
        
        # Verify physical file moved and active file is gone
        self.assertFalse(active_path.exists())
        expected_dest_path = self.test_removed_images_dir / f"{image_id}{staged_filepath.suffix}"
        self.assertTrue(expected_dest_path.exists())
        with open(expected_dest_path, 'rb') as f:
            self.assertEqual(f.read(), self.dummy_image_content)

        # Verify metadata filename path and file_moved_successfully flag
        self.assertEqual(self.removed_images[image_id]['filename'], f'removed/{image_id}{staged_filepath.suffix}')
        self.assertTrue(self.removed_images[image_id]['file_moved_successfully'])

        # Verify data is persisted
        loaded_active, loaded_removed = image_manager.load_all_images()
        self.assertNotIn(image_id, loaded_active)
        self.assertIn(image_id, loaded_removed)


    def test_remove_image_file_not_found(self):
        staged_filepath = self._create_dummy_staged_image()
        image_id, _ = image_manager.add_image(self.sample_image_params, staged_filepath, self.active_images, self.removed_images)
        
        # Manually delete the file to simulate external deletion
        os.remove(self.test_active_images_dir / f"{image_id}{staged_filepath.suffix}")

        # Test removing when file is already gone
        success = image_manager.remove_image(image_id, self.active_images, self.removed_images)
        self.assertFalse(success) # Expect move to fail
        self.assertNotIn(image_id, self.active_images) # Metadata should still be moved
        self.assertIn(image_id, self.removed_images)
        self.assertFalse(self.removed_images[image_id]['file_moved_successfully']) # Verify flag

        # Verify data is persisted with correct flag
        loaded_active, loaded_removed = image_manager.load_all_images()
        self.assertNotIn(image_id, loaded_active)
        self.assertIn(image_id, loaded_removed)
        self.assertFalse(loaded_removed[image_id]['file_moved_successfully'])


    def test_restore_image_success(self):
        staged_filepath = self._create_dummy_staged_image()
        image_id, _ = image_manager.add_image(self.sample_image_params, staged_filepath, self.active_images, self.removed_images)
        image_manager.remove_image(image_id, self.active_images, self.removed_images) # First remove it

        # Verify initial removed state
        removed_path = self.test_removed_images_dir / f"{image_id}{staged_filepath.suffix}"
        self.assertTrue(removed_path.exists())

        # Test restoring a removed image
        success = image_manager.restore_image(image_id, self.active_images, self.removed_images)
        self.assertTrue(success)
        self.assertIn(image_id, self.active_images)
        self.assertNotIn(image_id, self.removed_images)

        # Verify physical file moved and removed file is gone
        self.assertFalse(removed_path.exists())
        expected_dest_path = self.test_active_images_dir / f"{image_id}{staged_filepath.suffix}"
        self.assertTrue(expected_dest_path.exists())
        with open(expected_dest_path, 'rb') as f:
            self.assertEqual(f.read(), self.dummy_image_content)

        # Verify metadata filename path and file_moved_successfully flag
        self.assertEqual(self.active_images[image_id]['filename'], f'active/{image_id}{staged_filepath.suffix}')
        self.assertTrue(self.active_images[image_id]['file_moved_successfully'])

        # Verify data is persisted
        loaded_active, loaded_removed = image_manager.load_all_images()
        self.assertIn(image_id, loaded_active)
        self.assertNotIn(image_id, loaded_removed)

    def test_restore_image_file_not_found(self):
        staged_filepath = self._create_dummy_staged_image()
        image_id, _ = image_manager.add_image(self.sample_image_params, staged_filepath, self.active_images, self.removed_images)
        image_manager.remove_image(image_id, self.active_images, self.removed_images) # First remove it

        # Manually delete the file to simulate external deletion from removed
        os.remove(self.test_removed_images_dir / f"{image_id}{staged_filepath.suffix}")

        # Test restoring when file is already gone
        success = image_manager.restore_image(image_id, self.active_images, self.removed_images)
        self.assertFalse(success) # Expect move to fail
        self.assertIn(image_id, self.active_images) # Metadata should still be moved
        self.assertNotIn(image_id, self.removed_images)
        self.assertFalse(self.active_images[image_id]['file_moved_successfully']) # Verify flag

        # Verify data is persisted with correct flag
        loaded_active, loaded_removed = image_manager.load_all_images()
        self.assertIn(image_id, loaded_active)
        self.assertNotIn(image_id, loaded_removed)
        self.assertFalse(loaded_active[image_id]['file_moved_successfully'])


    def test_list_images(self):
        staged_filepath_1 = self._create_dummy_staged_image("img1.png")
        staged_filepath_2 = self._create_dummy_staged_image("img2.jpg")
        staged_filepath_3 = self._create_dummy_staged_image("img3.png")

        img1_params = self.sample_image_params.copy()
        img1_params.update({'aesthetic_rating': 'human_friendly', 'resolution': 512, 'colormap_name': 'twilight'})
        img1_id, _ = image_manager.add_image(img1_params, staged_filepath_1, self.active_images, self.removed_images)

        img2_params = self.sample_image_params.copy()
        img2_params.update({'aesthetic_rating': 'data_friendly', 'resolution': 1024, 'colormap_name': 'glasbey'})
        img2_id, _ = image_manager.add_image(img2_params, staged_filepath_2, self.active_images, self.removed_images)

        img3_params = self.sample_image_params.copy()
        img3_params.update({'aesthetic_rating': 'experimental', 'resolution': 512, 'colormap_name': 'viridis'})
        img3_id, _ = image_manager.add_image(img3_params, staged_filepath_3, self.active_images, self.removed_images)

        # Move img1 to removed
        image_manager.remove_image(img1_id, self.active_images, self.removed_images)

        # Test listing all
        active, removed = image_manager.list_images(aesthetic_filter='all', status='all')
        self.assertEqual(len(active), 2) # img2, img3
        self.assertEqual(len(removed), 1) # img1
        self.assertIn(img2_id, active)
        self.assertIn(img3_id, active)
        self.assertIn(img1_id, removed)

        # Test aesthetic filter
        human_friendly_active, _ = image_manager.list_images(aesthetic_filter='human_friendly')
        self.assertEqual(len(human_friendly_active), 0) # img1 was human_friendly but is removed
        
        # Corrected test for aesthetic filter
        human_friendly_all_status_active, human_friendly_all_status_removed = image_manager.list_images(aesthetic_filter='human_friendly')
        self.assertEqual(len(human_friendly_all_status_active), 0) # No active human_friendly
        self.assertEqual(len(human_friendly_all_status_removed), 1) # img1 is human_friendly and removed
        self.assertIn(img1_id, human_friendly_all_status_removed)

        data_friendly_active, _ = image_manager.list_images(aesthetic_filter='data_friendly')
        self.assertEqual(len(data_friendly_active), 1)
        self.assertIn(img2_id, data_friendly_active)

        # Test resolution filter
        res_512_active, res_512_removed = image_manager.list_images(resolution_filter=512)
        self.assertEqual(len(res_512_active), 1) # img3
        self.assertEqual(len(res_512_removed), 1) # img1
        self.assertIn(img3_id, res_512_active)
        self.assertIn(img1_id, res_512_removed)

        # Test colormap filter
        viridis_active, _ = image_manager.list_images(colormap_filter='viridis')
        self.assertEqual(len(viridis_active), 1)
        self.assertIn(img3_id, viridis_active)

        # Test combined filters
        filtered_active, filtered_removed = image_manager.list_images(
            aesthetic_filter='experimental', resolution_filter=512, colormap_filter='viridis'
        )
        self.assertEqual(len(filtered_active), 1)
        self.assertIn(img3_id, filtered_active)
        self.assertEqual(len(filtered_removed), 0)

    def test_purge_image_success(self):
        # Add an image, then remove it so it's in 'removed_images' and its file is in the removed directory
        staged_filepath = self._create_dummy_staged_image()
        image_id, _ = image_manager.add_image(self.sample_image_params, staged_filepath, self.active_images, self.removed_images)
        image_manager.remove_image(image_id, self.active_images, self.removed_images)
        
        # Verify it's in removed_images and its physical file exists in the removed directory
        self.assertIn(image_id, self.removed_images)
        removed_file_path = self.test_removed_images_dir / f"{image_id}{staged_filepath.suffix}"
        self.assertTrue(removed_file_path.exists())

        # Purge the image
        purged_data, success = image_manager.purge_image(image_id, self.active_images, self.removed_images)
        
        # Assertions for successful purge
        self.assertTrue(success)
        self.assertIsNotNone(purged_data)
        self.assertEqual(purged_data['resolution'], 1024) # Check some data from the purged image
        self.assertTrue(purged_data.get('physical_file_deleted')) # Verify the flag is True
        self.assertNotIn(image_id, self.removed_images) # Should no longer be in removed_images
        
        # Verify physical file is deleted
        self.assertFalse(removed_file_path.exists())

        # Verify persistence: load from file and check
        loaded_active, loaded_removed = image_manager.load_all_images()
        self.assertNotIn(image_id, loaded_active)
        self.assertNotIn(image_id, loaded_removed) # Crucially, should be gone from both

    def test_purge_image_not_in_removed(self):
        # Attempt to purge a non-existent image
        purged_data, success = image_manager.purge_image('image_999999', self.active_images, self.removed_images)
        self.assertFalse(success)
        self.assertIsNone(purged_data)
        self.assertEqual(len(self.active_images), 0)
        self.assertEqual(len(self.removed_images), 0)

    def test_purge_image_active(self):
        # Add an image, leave it in 'active_images'
        staged_filepath = self._create_dummy_staged_image()
        image_id, _ = image_manager.add_image(self.sample_image_params, staged_filepath, self.active_images, self.removed_images)
        self.assertIn(image_id, self.active_images)

        # Attempt to purge an active image (should fail)
        purged_data, success = image_manager.purge_image(image_id, self.active_images, self.removed_images)
        self.assertFalse(success)
        self.assertIsNone(purged_data)
        self.assertIn(image_id, self.active_images) # Should still be active
        self.assertNotIn(image_id, self.removed_images) # Should not have moved to removed

        # Verify persistence: load from file and check
        loaded_active, loaded_removed = image_manager.load_all_images()
        self.assertIn(image_id, loaded_active)
        self.assertNotIn(image_id, loaded_removed)
        
        # Verify physical file is still in active directory
        active_file_path = self.test_active_images_dir / f"{image_id}{staged_filepath.suffix}"
        self.assertTrue(active_file_path.exists())


    def test_purge_image_file_already_deleted(self):
        # Add an image, remove it, then manually delete its physical file
        staged_filepath = self._create_dummy_staged_image()
        image_id, _ = image_manager.add_image(self.sample_image_params, staged_filepath, self.active_images, self.removed_images)
        image_manager.remove_image(image_id, self.active_images, self.removed_images)
        
        removed_file_path = self.test_removed_images_dir / f"{image_id}{staged_filepath.suffix}"
        os.remove(removed_file_path) # Manually delete the file

        # Purge the image (metadata should still be purged, but file deletion flag should be False)
        purged_data, success = image_manager.purge_image(image_id, self.active_images, self.removed_images)
        
        self.assertTrue(success) # Metadata purge should still succeed
        self.assertIsNotNone(purged_data)
        self.assertFalse(purged_data.get('physical_file_deleted')) # Flag should be False
        self.assertNotIn(image_id, self.removed_images) # Metadata gone

        # Verify persistence
        loaded_active, loaded_removed = image_manager.load_all_images()
        self.assertNotIn(image_id, loaded_removed)


# To run these tests from the project root:
# python -m unittest tests/test_image_manager.py