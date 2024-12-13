import time
from datetime import datetime, timezone
# from pathlib import Path
from pprint import pprint

from PyQt6.QtCore import QThread, pyqtSignal, QRunnable, pyqtSlot, QObject
from pycomm3 import ResponseError

from scanner_lib import scan_cn, scan_bp, CommError, get_module_sn, get_backplane_sn

from global_data import global_data_cls
from saver import get_user_data_path

# global_data.restore_data()

TIME_FORMAT = '%Y%m%d_%H%M'

class PreScaner(QThread):
    """A scanner thread to perform modules scan"""
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    cn_node_current = pyqtSignal(str)
    communication_error = pyqtSignal(str)  # Signal if can't communicate
    module_found = pyqtSignal(dict)  # signal when found any module
    cn_nodes_found = pyqtSignal(list)  #signal when scan cn network complete

    def __init__(self, entry_point: str, deep_scan: bool = False, max_node_num = 99):
        super().__init__()
        self.entry_point = entry_point
        self.deep_scan = deep_scan
        self.found_paths_dict = {}
        self.scanned = set()
        self.max_node_num = max_node_num

    def _progress_update(self, *args, **kwargs):
        log_message = ' '.join(str(a) for a in args)
        self.progress.emit(log_message)

        for key, value in kwargs.items():
            self.progress.emit(f'{str(key)} = {str(value)}')
        pass

    def _current_cn_node_update(self, node: str):
        self.cn_node_current.emit(node)

    def _module_found(self, module: dict):
        pass
        # pprint(module)
        # self.module_found.emit(module)

    def run(self):
        try:
            ep = scan_bp(cip_path=self.entry_point,
                         p=self._progress_update,
                         module_found=self._module_found)
            bp_sn, modules, bp, cn_path = ep

            if self.deep_scan and len(cn_path):
                self.progress.emit('***************** Deep scan goes next...')
                for cn_serial, cip_path in cn_path.items():
                    controlnet_nodes, cn_modules_paths = scan_cn(cip_path,
                                                                 p=self._progress_update,
                                                                 current_cn_node_update=self._current_cn_node_update,
                                                                 max_node_num=self.max_node_num)
                    # global_data.cn_nodes.append(controlnet_nodes)
                    if len(controlnet_nodes) > 1:
                        for bp, _path in cn_modules_paths.items():
                            level1_bp = scan_bp(cip_path=_path, p=self._progress_update)
        except (CommError, ResponseError) as e:
            self.communication_error.emit(str(e))
            pass

        self.finished.emit()


class ScannerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        System name
    progress
        int indicating % progress

    '''
    start = pyqtSignal(str)
    finished = pyqtSignal(str)
    progress = pyqtSignal(str, str)
    cn_node_current = pyqtSignal(str)
    communication_error = pyqtSignal(str)  # Signal if can't communicate
    module_found = pyqtSignal(dict)  # signal when found any module


class Scanner(QRunnable):
    def __init__(self, system_name: str, entry_point: str, deep_scan: bool = True):
        super().__init__()
        self.system_name = system_name
        self.entry_point = entry_point
        self.deep_scan = deep_scan
        self.signals = ScannerSignals()
        utc_time = datetime.now(timezone.utc).strftime(TIME_FORMAT)
        fname = get_user_data_path() / 'prev' / f'{self.system_name}.{utc_time}.data'
        self.saver = global_data_cls(fname=fname)
        self.controlnet_modules_serial = set()
        self.backplane_serial = set()

    def _emit_progress(self, message):
        self.signals.progress.emit(self.system_name, message)

    def _module_found(self, module: dict):
        key = self._add_system_info_to_module(module)
        self.saver.module[key] = module
        self.signals.module_found.emit(module)

    def _add_system_info_to_module(self, module: dict):
        path_parts = module["path"].split('/')
        path_parts[0] = self.system_name
        system_path = '/'.join(path_parts)
        module["system"] = self.system_name
        return system_path


    @pyqtSlot()
    def run(self):
        self.signals.start.emit(self.system_name)
        self._emit_progress(f'Scanner start via Entry Point {self.entry_point}')

        try:
            self._scan_backplane(self.entry_point, 0)  # Start the recursive scan

        except CommError as e:
            self.signals.communication_error.emit(f"Communication Error: {e}")
        except ResponseError as e:
            self.signals.communication_error.emit(f"Response Error: {e}")
        except Exception as e:
            self.signals.communication_error.emit(f"Unexpected Exception: {e}")
        else:
            fname = get_user_data_path() / f'{self.system_name}.data'  # User data path
            self.saver.store_data()
            self.saver.store_data(filename=fname)
            self.signals.finished.emit(self.system_name)
        finally:
            print(f"Scanner complete {self.system_name}")


    def _scan_backplane(self, cip_path, level):
        self._emit_progress(f'Scanning Backplane Level {level}: {cip_path}')

        bp_sn, modules, bp, cn_path = scan_bp(
            cip_path=cip_path,
            p=lambda *args, **kwargs: self._emit_progress(' '.join(map(str, args))),  # Lambda for progress updates
            module_found=self._module_found
        )
        self.backplane_serial.add(bp_sn)



        if self.deep_scan and cn_path:
            self._emit_progress(f'Scanning ControlNet modules connected to Backplane Level {level}')
            for cn_serial, cn_cip_path in cn_path.items():
                if cn_serial in self.controlnet_modules_serial:
                    continue  # Skip already scanned ControlNet modules

                self.controlnet_modules_serial.add(cn_serial)
                try:
                    controlnet_nodes, communication_modules_paths = scan_cn(
                        cn_cip_path,
                        p=lambda *args, **kwargs: self._emit_progress(' '.join(map(str, args))),
                        current_cn_node_update=self.signals.cn_node_current.emit
                    )
                    self.saver.cn_nodes.append(controlnet_nodes)

                    for bp, path in communication_modules_paths.items():
                        backplane_serial = get_backplane_sn(path)
                        if backplane_serial and backplane_serial not in self.backplane_serial:
                            self._scan_backplane(path, level + 1) # Recursive call for next level


                except CommError as e:
                    self._emit_progress(f"Error scanning ControlNet {cn_cip_path}: {e}")