from icecream import ic
from PyQt6.QtCore import QThread, pyqtSignal
from scanner_lib import scan_cn, scan_bp, CommError

from global_data import global_data


class Scaner(QThread):
    """A scanner thread to perform modules scan"""
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    cn_node_current = pyqtSignal(str)
    communication_error = pyqtSignal(str)  # Signal if can't communicate

    def __init__(self, entry_point: str, deep_scan: bool = False):
        super().__init__()
        self.entry_point = entry_point
        self.deep_scan = deep_scan
        self.found_paths_dict = {}
        self.scanned = set()

    def _progress_update(self, *args, **kwargs):
        log_message = ' '.join(str(a) for a in args)
        self.progress.emit(log_message)

        for key, value in kwargs.items():
            self.progress.emit(f'{str(key)} = {str(value)}')
        pass

    def _current_cn_node_update(self, node: str):
        self.cn_node_current.emit(node)


    def run(self):
        global_data.flush()
        try:
            ep = scan_bp(cip_path=self.entry_point, entry_point=True, format='   ', p=self._progress_update)
            bp_sn, modules, bp, cn_path = ep

            if self.deep_scan and ic(len(cn_path)):
                self.progress.emit('***************** Deep scan goes next...')
                for cn_serial, cip_path in cn_path.items():
                    controlnet_nodes, cn_modules_paths = scan_cn(cip_path,
                                                                       p=self._progress_update,
                                                                       current_cn_node_update=self._current_cn_node_update
                                                                       )
                    global_data.cn_nodes.append(controlnet_nodes)
                    if len(controlnet_nodes) > 1:
                        for bp, p in cn_modules_paths.items():
                            level1_bp = scan_bp(cip_path=p, entry_point=False, format='   ', p=self._progress_update)
        except CommError as e:
            self.communication_error.emit(str(e))
            pass

        self.finished.emit()





