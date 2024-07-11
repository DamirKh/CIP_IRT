# module for storing global program data
import pickle
from copy import deepcopy


class global_data_obj(object):
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


global_data = global_data_obj()

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
    "cn_addr": None
}


def new_blank_module():
    return deepcopy(blank_module)
