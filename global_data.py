# module for storing global program data
import pickle
from copy import deepcopy

class comment_saver_cls(object):
    """
    A class to manage and persist comments associated with serial numbers,
    storing data in a plain text file.

    Attributes:
        _fname (str): The default filename for saving/loading comments.
        sn (dict): A dictionary storing serial numbers as keys and lists of
                   comment lines as values.

    Methods:
        __init__(self, fname='comments.txt'): Initializes the class with a
                                                  filename.
        get_comment(self, sn: str): Retrieves the comment for a given serial
                                      number.
        set_comment(self, sn: str, comment: str): Sets the comment for a given
                                                  serial number.
        save(self, filename=None): Saves the comments to a text file.
        load(self, filename=None): Loads comments from a text file.
    """
    def __init__(self, fname='comments.txt'):
        """
        Initializes the comment_saver_cls object.

        Args:
            fname (str, optional): The filename for saving/loading comments.
                                    Defaults to 'comments.txt'.
        """
        self._fname = fname
        self.sn = {}

    def get_comment(self, sn: str) -> str:
        """
        Retrieves the comment associated with a specific serial number.

        Args:
            sn (str): The serial number to get the comment for.

        Returns:
            str: The comment associated with the serial number, or an empty
                  string if not found.
        """
        comment_lines = self.sn.get(sn, [])
        return "\n".join(comment_lines)

    def set_comment(self, sn: str, comment: str):
        """
        Sets or updates the comment for a given serial number.

        Args:
            sn (str): The serial number to set the comment for.
            comment (str): The comment to be associated with the serial number.
        """
        self.sn[sn] = [line.lstrip() for line in comment.splitlines()]

    def save(self, filename: str = None):
        """
        Saves the comments dictionary to a text file.

        Args:
            filename (str, optional): The filename to save to. If None, uses
                                        the default _fname. Defaults to None.
        """
        fname = filename or self._fname
        with open(fname, 'w') as file:
            for sn, comment_lines in self.sn.items():
                file.write(f"{sn}\n")
                for line in comment_lines:
                    file.write(f"  {line}\n")
        print(f"Comments saved in {fname}")

    def load(self, filename: str = None):
        """
        Loads comments from a text file. Handles potential errors gracefully.

        Args:
            filename (str, optional): The filename to load from. If None, uses
                                         the default _fname. Defaults to None.
        """
        fname = filename or self._fname
        self.sn = {}
        try:
            with open(fname, 'r') as file:
                current_sn = None
                for line in file:
                    line = line.rstrip('\n')  # Remove trailing newline
                    if line.startswith("#"):  # ignore line
                        continue
                    if line.startswith("  "):  # Comment line
                        try:
                            self.sn[current_sn].append(line.lstrip())  # Remove leading spaces
                        except AttributeError:
                            # Skip lines at the top of file while not found SN
                            continue
                        except KeyError:
                            self.sn[current_sn] = []
                            self.sn[current_sn].append(line.lstrip())  # second try
                    else:  # Serial number line
                        current_sn = line.split(sep=" ")[0]
                        # self.sn[current_sn] = []
        except FileNotFoundError:
            print(f"No {fname} yet! Let's create one")
            self.save(filename=fname)

class global_data_cls(object):
    def __init__(self, fname='global.data'):
        self.__fname = fname
        self.entry_point = {}
        self.module = {}
        self.bp = {}
        self.cn_flex = {}
        self.cn_nodes = []

    def flush(self):
        """remove all datas"""
        self.entry_point = {}
        self.module = {}
        self.bp = {}
        self.cn_flex = {}
        self.cn_nodes = []

    def store_data(self, filename=None):
        """Stores data using pickle.

      Args:
        filename: The name of the file to store the data in.
      """
        fname = filename or self.__fname
        data = {
            'entry_point': self.entry_point,
            'module': self.module,
            'bp': self.bp,
            'cn_flex': self.cn_flex,
            'cn_nodes': self.cn_nodes
        }
        with open(fname, 'wb') as file:
            pickle.dump(data, file)
        print(f"Data [{self.entry_point}] saved in {fname}")

    def restore_data(self, filename=None):
        """Restores data from a pickle file.

        Args:
        filename: The name of the file containing the pickled data.

        Returns:
        The restored data.
        """
        fname = filename or self.__fname
        with open(fname, 'rb') as file:
            data = pickle.load(file)
            self.entry_point = data['entry_point']
            self.module = data['module']
            self.bp = data['bp']
            self.cn_flex = data['cn_flex']
            self.cn_nodes = data['cn_nodes']
            return data


global_data = global_data_cls()

current_comment_saver = None

blank_module = {
    "system": None,
    "vendor#": None,
    "product_type#": None,
    "product_code": None,
    "major": None,
    "minor": None,
    "status": None,
    "serial": None,
    "product_name": None,
    "product_type": None,
    "vendor": None,
    "rev": None,
    "slot": None,
    "size": None,
    "path": None,
    "name": None,
    "cn_node": None
}


def new_blank_module():
    return deepcopy(blank_module)
