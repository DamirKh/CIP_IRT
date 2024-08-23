import time
from datetime import datetime, timezone
from pprint import pprint

from PyQt6.QtCore import QThread, pyqtSignal, QRunnable, pyqtSlot, QObject
from scanner_lib import scan_cn, scan_bp, CommError, get_module_sn, get_backplane_sn

from global_data import global_data_obj
from saver import get_user_data_path

# global_data.restore_data()

TIME_FORMAT='%Y-%m-%d_%H:%M'

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
        except CommError as e:
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
    finished = pyqtSignal(str)
    progress = pyqtSignal(str, str)
    cn_node_current = pyqtSignal(str)
    communication_error = pyqtSignal(str)  # Signal if can't communicate
    module_found = pyqtSignal(dict)  # signal when found any module


class Scaner(QRunnable):
    """A scanner thread to perform modules scan"""


    def __init__(self, system_name: str, entry_point: str, finish_callback,  deep_scan: bool = True):
        super(Scaner, self).__init__()
        # s = SystemConfigSaver(filename=f'{system_name}.json')
        # system_settings = s.load_data()
        self.system_name = system_name
        self.entry_point = entry_point
        self.deep_scan = deep_scan
        self.found_paths_dict = {}
        self.signals = ScannerSignals()
        utc_time = datetime.now(timezone.utc).strftime(TIME_FORMAT)
        fname = get_user_data_path() / 'prev' / f'{self.system_name}.{utc_time}.data'
        self.saver = global_data_obj(fname=fname)  # check it
        self.controlnet_modules_serial = set([])
        self.backplane_serial = set([])
        # self.finish_callback = finish_callback
        # self.scanned = set()

    def _progress_update(self, *args, **kwargs):
        log_message = ' '.join(str(a) for a in args)
        self.signals.progress.emit(self.system_name, log_message)

        for key, value in kwargs.items():
            self.signals.progress.emit(self.system_name, f'{str(key)} = {str(value)}')
        pass

    def _current_cn_node_update(self, node: str):
        self.signals.cn_node_current.emit(node)

    def _module_found(self, module: dict):
        key = self._module_found_print(module)
        self.saver.module[key] = module
        self.signals.module_found.emit(module)

    def _module_found_print(self, module: dict):
        # pprint(module)
        path_ip = module["path"].split('/')
        path_ip[0] = self.system_name
        path_system_name = '/'.join(path_ip)
        module["system"] = self.system_name
        # key = f"{self.system_name}/{module['serial']}"
        key = path_system_name
        # pprint(key)
        # pprint(module, indent=2)
        return key

    @pyqtSlot()
    def run(self):
        print(f'Scaner start {self.system_name}')
        self.saver.flush()
        try:
            ep = scan_bp(cip_path=self.entry_point,
                         p=self._progress_update,
                         module_found=self._module_found
                         )
            bp_sn, modules, bp, cn_path = ep
            self.backplane_serial.add(bp_sn)
            for cn_serial in cn_path.keys():
                self.controlnet_modules_serial.add(cn_serial)

            if self.deep_scan and len(cn_path):
                self.signals.progress.emit(self.system_name, '***************** Deep scan goes next...')
                for cn_serial, cip_path in cn_path.items():
                    try:
                        controlnet_nodes, cn_modules_paths = scan_cn(cip_path,
                                                                     p=self._progress_update,
                                                                     current_cn_node_update=self._current_cn_node_update
                                                                     )
                    except CommError:
                        print(f'Error scanning ControlNet {cip_path} !')
                    self.saver.cn_nodes.append(controlnet_nodes)
                    if len(controlnet_nodes) > 1:  # more than one node in CN network found
                        for bp, p in cn_modules_paths.items():
                            controlnet_serial = get_module_sn(p)
                            backplane_serial = get_backplane_sn(p)
                            if controlnet_serial and controlnet_serial in self.controlnet_modules_serial:
                                continue
                            if backplane_serial and backplane_serial in self.backplane_serial:
                                continue
                            if controlnet_serial:
                                self.controlnet_modules_serial.add(controlnet_serial)
                            if backplane_serial:
                                self.backplane_serial.add(backplane_serial)
                            try:
                                level1_bp = scan_bp(cip_path=p,
                                                    p=self._progress_update,
                                                    module_found=self._module_found
                                                    )
                            except CommError:
                                print(f'Error scanning Backplane {cip_path} !')

            if not len(cn_path):
                self.signals.progress.emit(self.system_name, '***************** No ControlNet modules in this BackPlane')
                ep = scan_bp(cip_path=self.entry_point,
                         module_found=self._module_found
                         )

        except CommError as e:
            self.signals.communication_error.emit(self.system_name)
            # self.saver.flush()
            # self.saver.restore_data()
            pass
        else:
            fname = get_user_data_path() / f'{self.system_name}.data'
            self.saver.store_data()
            self.saver.store_data(filename=fname)
            print(f"Data saved: {get_user_data_path() / f'{self.system_name}.data'}")
            self.signals.finished.emit(self.system_name)
        finally:
            print(f"Scanner complete {self.system_name}")
            # self.finish_callback(self.system_name)
