import time
from datetime import datetime, timezone
from pprint import pprint

from PyQt6.QtCore import QThread, pyqtSignal, QRunnable, pyqtSlot, QObject
from scanner_lib import scan_cn, scan_bp, CommError, get_module_sn, get_backplane_sn

from global_data import global_data_obj
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
    start = pyqtSignal(str)
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
        """add system name to the module
        returns key which is  module['path'] with replaced IP by system name"""
        path_ip = module["path"].split('/')
        path_ip[0] = self.system_name
        path_system_name = '/'.join(path_ip)
        module["system"] = self.system_name
        # key = f"{self.system_name}/{module['serial']}" # may be later
        key = path_system_name
        return key

    @pyqtSlot()
    def run(self):
        def emit(message):
            self.signals.progress.emit(self.system_name, message)
        self.signals.start.emit(self.system_name)
        emit(f'Scaner start via Entry Point {self.entry_point}')

        self.saver.flush()
        try:
            emit('***************** Scanning Entry Point...')
            ep = scan_bp(cip_path=self.entry_point,
                         p=self._progress_update,
                         module_found=self._module_found
                         )
            bp_sn, modules, bp, cn_path = ep
            self.backplane_serial.add(bp_sn)
            for cn_serial in cn_path.keys():
                self.controlnet_modules_serial.add(cn_serial)

            if self.deep_scan and len(cn_path):
                emit('***************** Scanning ControlNet Level 0 goes next...')
                for cn_serial, cip_path in cn_path.items():  # scans controlnets via each CN module in entry point Backplane
                    try:
                        controlnet_nodes, cn_modules_paths = scan_cn(cip_path,
                                                                     p=self._progress_update,
                                                                     current_cn_node_update=self._current_cn_node_update
                                                                     )
                    except CommError:
                        # print(f'Error scanning ControlNet {cip_path} !')
                        emit('Error scanning ControlNet {cip_path} !')
                    else:
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
                                    # this will scan backplanes via controlnet
                                    # only backplanes which
                                    # 1. backplane's SN not seen before
                                    # 2. ControlNet module's SN not seen before
                                    # * * * * LEVEL 1
                                    emit(f'Scan BackPlane Level 1 {p}')
                                    level1_bp = scan_bp(cip_path=p,
                                                        p=self._progress_update,
                                                        module_found=self._module_found
                                                        )
                                    bp_sn_l1, modules_l1, bp_l1, cn_path_l1 = level1_bp
                                    self.backplane_serial.add(bp_sn_l1)
                                    for cn_serial_l1 in cn_path_l1.keys():
                                        self.controlnet_modules_serial.add(cn_serial_l1)
                                    emit('***************** Scanning ControlNet Level 1 goes next...')
                                    for cn_serial_l1, cip_path_l1 in cn_path_l1.items():  # scans controlnets via each CN module in Backplane level 1
                                        try:
                                            controlnet_nodes_l1, cn_modules_paths_l1 = scan_cn(cip_path_l1,
                                                                                         p=self._progress_update,
                                                                                         current_cn_node_update=self._current_cn_node_update
                                                                                         )
                                        except CommError:
                                            # print(f'Error scanning ControlNet {cip_path} !')
                                            emit(f'Error scanning ControlNet {cip_path} !')
                                        else:
                                            self.saver.cn_nodes.append(controlnet_nodes)
                                            if len(controlnet_nodes_l1) > 1:  # more than one node in CN network found
                                                for bp, p in cn_modules_paths_l1.items():
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
                                                        # * * * * LEVEL 2
                                                        emit(f'Scan BackPlane Level 2 {p}')
                                                        level2_bp = scan_bp(cip_path=p,
                                                                            p=self._progress_update,
                                                                            module_found=self._module_found
                                                                            )
                                                        bp_sn_l2, modules_l2, bp_l2, cn_path_l2 = level2_bp
                                                        if len(cn_path_l2.keys())>1:
                                                            emit(f'Probably there are level 2 ControlNet existing in BackPlane {p}')
                                                    except CommError:
                                                        emit(f'Error scanning Backplane level 2{cip_path} !')

                                except CommError:
                                    print(f'Error scanning Backplane level 1 {cip_path} !')

            if not len(cn_path):
                emit('***************** No ControlNet modules in this BackPlane')
                # does next really need?
                # ep = scan_bp(cip_path=self.entry_point,
                #          module_found=self._module_found
                #          )
            if not self.deep_scan and len(cn_path):
                emit(f'*** WARNING: Deep scan not checked, but found {len(cn_path)} ControlNet modules!')


        except CommError as e:
            self.signals.communication_error.emit(self.system_name)
            # self.saver.flush()
            # self.saver.restore_data()
            pass
        else:
            fname = get_user_data_path() / f'{self.system_name}.data'
            self.saver.store_data()
            self.saver.store_data(filename=fname)
            self.signals.finished.emit(self.system_name)
        finally:
            print(f"Scanner complete {self.system_name}")
