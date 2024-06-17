from collections import namedtuple

from icecream import ic

from pycomm3 import CIPDriver, Services, DataTypes
from pycomm3.exceptions import ResponseError, RequestError, CommError

from global_data import Entry_point

scanned_bp = set([])
scanned_cn = set([])


class Discover(object):
    """
    Scans a whole system
    """

    def __init__(self, entry_point):
        """
        Initializes the Discover object.

        Args:
            entry_point (str): The IP address or hostname of the entry point for scanning.
        """
        self.entry_point = entry_point
        self.discovered_nodes = {}  # {serial_number: (cip_path, scanned)}
        self.bps = {}
        self.cn_nodes = []
        self.scan_complete = False


    def run(self):
        """
        """
        bp_sn, fs, devices = scan_bp(self.entry_point)
        self.bps[bp_sn] = devices

        for controlnet_sn in fs.keys():
            cip_path, already_scanned = fs[controlnet_sn]
            if not already_scanned:
                nodes = scan_cn(cip_path)
            # print(nodes)


        self.cn_nodes = nodes


def scan_bp(cip_path):
    """
    Scans the specified CIP path for modules and returns a dictionary
    mapping their serial numbers to their corresponding paths and whether they've been scanned.

    Args:
        cip_path (str): The CIP path to scan.

    Returns:
        dict: A dictionary where keys are serial numbers of modules,
              and values are tuples containing the module's path and a boolean indicating
              whether it's been scanned.
    """
    future_scan = {}
    backplane_sn = None
    devices = []

    driver = CIPDriver(cip_path)
    driver.open()
    for slot in range(14):
        try:
            device = driver.get_module_info(slot)
            module_serial_number = device['serial']
            module_product_code = device['product_code']
            # print(f'{slot}: {device['product_name']}')
            # print(device)

            # Check for ControlNet modules (product_code 22)
            if module_product_code == 22:
                ic(f'controlnet in slot {slot}')
                # Add to future_scan if not already present
                if module_serial_number in future_scan.keys():
                    pass
                else:
                    future_scan[module_serial_number] = (
                        f'{cip_path}/bp/{slot}/cnet',
                        False  # Initially set to False (not scanned)
                    )
            if module_product_code in (93, 22, 166):  # processor, controlnet or ethernet
                ic(f'Intelligent in slot {slot}')
                p = f'{cip_path}/bp/{slot}'
                plc_driver = CIPDriver(p)
                plc_driver.open()
                backplane_serial_number_raw = plc_driver.generic_message(
                    service=Services.get_attributes_all,
                    class_code=0x66,
                    instance=0x1,
                    attribute=0x0,
                    # data_type=DataTypes.dint[10],
                    connected=False,
                    unconnected_send=True,
                    route_path=True,
                )
                plc_driver.close()
                discovered_bp_sn = ic(decode_serial_number(backplane_serial_number_raw.value))

                if backplane_sn is None and discovered_bp_sn:
                    backplane_sn = discovered_bp_sn
                if backplane_sn is not None and discovered_bp_sn:
                    assert backplane_sn == discovered_bp_sn

        except  ResponseError:
            ic(f'no module in slot {slot} or no slot')
            continue
        devices.append(device)

    driver.close()
    return backplane_sn, future_scan, devices


def scan_cn(cip_path):
    found_controlnet_nodes = []
    print(f'Scaning {cip_path}...')
    for cnet_node_num in range(100):
        target = f'{cip_path}/{cnet_node_num}/bp/0'
        # print(f' Scan address {cnet_node_num}')
        try:
            driver = CIPDriver(target)
            driver.open()
            for slot in range(13):
                try:
                    device = driver.get_module_info(slot)
                    # print(f'Slot {slot}')
                    # print(device)

                    if device['product_code'] == 22:
                        print(f'ControlNet module at slot {cnet_node_num}/{slot}')
                        if not cnet_node_num in found_controlnet_nodes:
                            found_controlnet_nodes.append(cnet_node_num)
                        # future_scan.append(f'{entry_point}/bp/{slot}/cnet/')
                        pass
                except ResponseError:
                    pass
                    # print("Response ERROR")
            driver.close()
        except ResponseError:
            print('.', end='')
            driver.close()
    return found_controlnet_nodes


def decode_serial_number(data):
    """Decodes a byte string representing a serial number into a hexadecimal string.

      Args:
        data: A byte string containing the serial number data.

      Returns:
        A string containing the hexadecimal representation of the serial number.
      """

    # Select 4 bytes with SN
    serial_bytes = data[12:16]

    # Reverse the byte order
    serial_bytes = serial_bytes[::-1]

    # Convert to hexadecimal string, removing leading '0x' and spaces
    hex_serial = serial_bytes.hex().upper().replace('0x', '').replace(' ', '')

    return hex_serial


if __name__ == '__main__':
    # this function here jast an example for coding purpose
    # Example usage decode_serial_number
    # data = b'\x00\x08\x00\x00\x00\x00\x04\x00\x00\x00\x01\x01\xef\xa5\x1a\x00\x00'
    # decoded_serial = decode_serial_number(data)
    # print(f"Decoded Serial Number: {decoded_serial}")

    print('Scanner lib standalone running')
    ic.disable()

    test_entry = '11.80.18.1'
    # bp_sn, fs = scan_bp(test_entry)
    # ic(bp_sn)
    # ic(fs)
    # for controlnet_sn in fs.keys():
    #     cip_path, already_scanned = fs[controlnet_sn]
    #     if not already_scanned:
    #         nodes = scan_cn(cip_path)
    #     print(nodes)
    #
    # pass

    d = Discover(test_entry)
    d.run()
    pass
    print(d.cn_nodes)
    print(d.bps)
