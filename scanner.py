import time
from icecream import ic
from PyQt6.QtCore import QThread, pyqtSignal

from pycomm3 import CIPDriver
from pycomm3.exceptions import ResponseError, RequestError, CommError


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


    def scan_bp(self, cip_path):
        driver = CIPDriver(cip_path)  # Need a separate driver for each backplane
        try:
            self.progress.emit(f'Waiting for connection to {cip_path}...')
            driver.open()
        except CommError:
            self.progress.emit(f'Failed to open a connection to {cip_path}')
            self.finished.emit()
            return

        self.progress.emit(f'Connected to {cip_path}')

        for slot in range(13):
            device = self.check_module(driver, slot)
            if device is False or device is True:
                continue
            serial_number = device['serial']
            ic(device)

            self.progress.emit(f'Slot {slot}')
            self.progress.emit(device["product_name"])
            if device['product_code'] == 22:
                # self.progress.emit(f'ControlNet module at slot {slot}')
                if not serial_number in self.found_paths_dict.keys():  # First hit
                    self.progress.emit(f'Found ControlNet module at slot {slot}: {device["product_name"]}')
                    self.found_paths_dict[serial_number] = f'{cip_path}/bp/{slot}/cnet'
                    # self.found_paths_dict[serial] = f'{cip_path}/bp/{slot}/cnet/bp/0'
        driver.close()

    def scan_cn(self, cip_path):
        print(f'Scaning {cip_path}...')
        for cnet_node_num in range(100):
            target = f'{cip_path}/{cnet_node_num}/bp/0'
            # print(f' Scan address {cnet_node_num}')
            try:
                driver = CIPDriver(target)
                driver.open()
                for slot in range(13):
                    device = self.check_module(driver, slot)
                    if device is False or device is True:
                        continue
                    ic(device)

                    if device['product_code'] == 22:
                        print(f'ControlNet module at slot {slot}')
                        # future_scan.append(f'{entry_point}/bp/{slot}/cnet/')
                        pass
                driver.close()
            except RequestError:
                print('.', end='')
                driver.close()

    def check_module(self, driver: CIPDriver, slot: int):
        try:
            device = driver.get_module_info(slot)
            serial_number = device['serial']
            if serial_number in self.scanned:
                return True
            else:
                self.scanned.add(serial_number)
                return device

        except RequestError:
            print('.', end='')
            return False
        except ResponseError:
            pass
            # self.progress.emit("Response ERROR")
            # ic(f"No device in slot {slot}")
            return False
