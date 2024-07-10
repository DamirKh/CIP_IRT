import json
import pathlib
from .config_path import get_user_data_path


class ModuleSaver:
    """
    This module stores information about scanned objects.
    """

    def __init__(self, dir=None, filename="scanned_objects.json"):
        if dir is None:
            dir = pathlib.Path(get_user_data_path())  # Use the provided function
        else:
            dir = pathlib.Path(dir)  # Make sure 'dir' is a pathlib.Path object

        self.filename = dir / filename
        self.data = self.load_data()

    def load_data(self):
        """
        Loads existing object data from the JSON file.
        """
        try:
            with open(self.filename, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}  # Return an empty dict if no file exists

    def save_data(self):
        """
        Saves the object data to the JSON file.
        """
        try:
            with open(self.filename, "w") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")

    def add_object(self, object_info):
        """
        Adds information about a new object to the data store.
        """
        object_id = object_info.get("serial")
        if object_id:
            self.data[object_id] = object_info
            self.save_data()
            print(f"Object with serial {object_id} added successfully.")
        else:
            print("Error: Object information must include a 'serial'.")

    def get_object(self, object_id):
        """
        Retrieves information about a specific object.
        """
        return self.data.get(object_id)


# Example usage in your main program
if __name__ == "__main__":
    scanner = ModuleSaver()  # Use the default directory

    # Example object information
    object1 = {"serial": "scanner-123", "name": "Box", "size": "Large", "location": "Room A"}
    scanner.add_object(object1)

    # Retrieve information about the scanned object
    object_info = scanner.get_object("scanner-123")
    print(f"Retrieved object information: {object_info}")

    # Example usage with a custom directory
    custom_dir = pathlib.Path("./data")  # Create a directory 'data' for example
    custom_scanner = ModuleSaver(dir=custom_dir)
    custom_scanner.add_object({"serial": "custom-object-1", "name": "Custom Object"})
