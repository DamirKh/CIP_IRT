import time
from icecream import ic
from PyQt6.QtCore import QThread, pyqtSignal


class Scaner(QThread):
    """A scanner thread to perform modules scan"""
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    found_paths = pyqtSignal(dict)  # Signal to emit a list of paths

    def __init__(self, entry_point: str, deep_scan: bool = False):
        super().__init__()
        self.entry_point = entry_point
        self.deep_scan = deep_scan
        self.found_paths_dict = {}
        self.scanned = set()

    def run(self):
        self.scan_bp(self.entry_point)
        if self.deep_scan and ic(len(self.found_paths_dict)):
            print('Deep scan here...')
            for cn_module in self.found_paths_dict.keys():
                self.scan_cn(self.found_paths_dict[cn_module])
        self.finished.emit()





