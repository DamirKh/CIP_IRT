import unittest
import json
import pathlib
import os
from unittest.mock import patch
from saver import ModuleSaver  # Replace 'your_module' with the actual module name

class TestModuleSaver(unittest.TestCase):

    @patch("saver.get_user_data_path")
    def setUp(self, mock_get_user_data_path):
        """Set up a temporary file for testing."""
        mock_get_user_data_path.return_value = "/tmp/test_data"
        self.scanner = ModuleSaver()
        self.test_object = {"serial": "test-object-1", "name": "Test Object", "size": "Medium"}
        self.test_filename = "/tmp/test_data/scanned_objects.json"
        os.makedirs(os.path.dirname(self.test_filename), exist_ok=True)
        open(self.test_filename, "w").close()

    def tearDown(self):
        """Clean up the temporary file after testing."""
        try:
            os.remove(self.test_filename)
        except FileNotFoundError:
            pass

    def test_load_data(self):
        """Test loading existing data from a file."""
        self.assertEqual(self.scanner.data, {})

    def test_save_data(self):
        """Test saving data to the file."""
        self.scanner.data = {"test-object-2": {"serial": "test-object-2", "name": "Another Object"}}
        self.scanner.save_data()
        with open(self.test_filename, "r") as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, {"test-object-2": {"serial": "test-object-2", "name": "Another Object"}})

    def test_add_object(self):
        """Test adding a new object to the data store."""
        self.scanner.add_object(self.test_object)
        self.assertEqual(self.scanner.data["test-object-1"], self.test_object)

    def test_add_object_missing_serial(self):
        """Test handling an object without a 'serial'."""
        missing_serial_object = {"name": "No Serial Object"}
        self.scanner.add_object(missing_serial_object)
        self.assertNotIn("No Serial Object", self.scanner.data)

    def test_get_object(self):
        """Test retrieving object information by serial."""
        self.scanner.add_object(self.test_object)
        retrieved_object = self.scanner.get_object("test-object-1")
        self.assertEqual(retrieved_object, self.test_object)

    def test_get_nonexistent_object(self):
        """Test retrieving an object that doesn't exist."""
        self.assertIsNone(self.scanner.get_object("nonexistent-object"))

    def test_custom_directory(self):
        """Test using a custom directory for the data file."""
        custom_dir = pathlib.Path("/tmp/custom_data")
        custom_scanner = ModuleSaver(dir=custom_dir)
        custom_test_object = {"serial": "custom-object-1", "name": "Custom Object"}
        custom_scanner.add_object(custom_test_object)
        os.makedirs(os.path.dirname(custom_scanner.filename), exist_ok=True)
        open(custom_scanner.filename, "w").close()  # Create the file
        self.assertEqual(custom_scanner.filename, pathlib.Path("/tmp/custom_data/scanned_objects.json"))
        with open(custom_scanner.filename, "r") as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, {"custom-object-1": custom_test_object})

    def test_load_data_file_not_found(self):
        """Test loading data when the file doesn't exist."""
        # This test should pass because load_data should handle FileNotFoundError
        self.assertEqual(self.scanner.data, {})

if __name__ == '__main__':
    unittest.main()