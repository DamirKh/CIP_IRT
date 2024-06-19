from collections import namedtuple

from icecream import ic

from pycomm3 import CIPDriver, Services, DataTypes
from pycomm3.exceptions import ResponseError, RequestError, CommError
from pycomm3 import parse_connection_path

from global_data import Entry_point

bp_all = set([])
full_map = {}

controlnet_module = 22
flex_adapter = 37
intellectual_module = (
    22,  # controlnet
    166, # ethernet
    37,  # FlexIO CN adapter
)
plc_module = 93
serial_unknown = 'FFFFFFFF'


class AlreadyScanned(Exception):
    """Custom exception to indicate a backplane has already been scanned."""

    def __init__(self, bp_serial):
        super().__init__(f"Backplane with serial {bp_serial} has already been scanned.")


class BackplaneSerialNumberMissmatch(Exception):
    """an exception occurs when the backplane serial number does not match the current serial number"""

    def __init__(self, bp_serial_current, bp_serial_prev):
        super().__init__(f"Backplane SN {bp_serial_current} != {bp_serial_prev}")


def scan_bp(cip_path, format='', exclude_bp_sn=''):
    """
    Scans the Backplane by specified CIP path for modules and returns a dictionary
    mapping their serial numbers to their corresponding paths and whether they've been scanned.

    Args:
        cip_path (str): The CIP path to scan.

    Returns:
        dict: A dictionary where keys are serial numbers of modules,
              and values are tuples containing the module's path and a boolean indicating
              whether it's been scanned.
    """
    print(f'{format}Scanning BackPlane at {cip_path}')

    this_bp = {}
    this_bp_sn = serial_unknown
    modules_all = set([])
    cn_modules_paths = {}

    # devices = []

    _p = parse_connection_path(cip_path)
    driver = CIPDriver(cip_path)
    driver.open()
    for slot in range(14):
        try:
            device = driver.get_module_info(slot)
            this_bp[slot] = ic(device)
            module_serial_number = device['serial']
            modules_all.add(module_serial_number)
            module_product_code = device['product_code']

            if module_product_code == 37:
                print(f'FlexIO at {cip_path}')

            if module_product_code in intellectual_module or module_product_code == plc_module:  # controlnet, ethernet or processor
                ic(f'Intelligent in slot {slot}')
                p = f'{cip_path}/bp/{slot}'
                plc_driver = CIPDriver(p)
                plc_driver.open()
                # https://www.plctalk.net/threads/rockwell-plc-chassis-serial-number-rs-logix.86426/
                backplane_serial_number_raw = plc_driver.generic_message(
                    service=Services.get_attributes_all,
                    class_code=0x66,
                    instance=0x1,
                    attribute=0x0,
                    # data_type=DataTypes.dint[10],
                    connected=False,
                    unconnected_send=True,
                    route_path=True
                    # route_path=f'bp/{slot}'
                )
                plc_driver.close()
                bp_serial_current = ic(decode_serial_number(backplane_serial_number_raw.value))
                if this_bp_sn == serial_unknown:
                    this_bp_sn = bp_serial_current
                elif this_bp_sn != bp_serial_current:
                    raise BackplaneSerialNumberMissmatch(bp_serial_current, this_bp_sn)

            if module_product_code == controlnet_module:
                ic(f'controlnet in slot {slot}')
                cn_modules_paths[module_serial_number] = f'{cip_path}/bp/{slot}/cnet'

        except  ResponseError:
            ic(f'no module in slot {slot} or no slot')
            continue
        # except AlreadyScanned:
        #     ic(f'Backplane {discovered_bp_sn} has already been scanned. Skip it')
        #     skip_this_bp = True
        #     break

    driver.close()

    return this_bp_sn, this_bp, cn_modules_paths


def scan_cn(cip_path, format='', exclude_bp_sn=''):
    cn_modules_paths = {}
    found_controlnet_nodes = []
    print(f'Scanning ControlNet {cip_path}...')
    for cnet_node_num in range(100):
        target = f'{cip_path}/{cnet_node_num}/bp/0'
        # print(f' Scan address {cnet_node_num}')
        try:
            driver = CIPDriver(target)
            driver.open()
            for slot in range(14):
                try:
                    device = driver.get_module_info(slot)
                    # print(f'Slot {slot}')
                    # print(device)

                    if device['product_code'] == controlnet_module or device['product_code'] == flex_adapter:
                        print(f'ControlNet module at slot {cnet_node_num}/{slot}')
                        if not cnet_node_num in found_controlnet_nodes:
                            found_controlnet_nodes.append(cnet_node_num)
                        cn_modules_paths[device['serial']] = f'{cip_path}/{cnet_node_num}/bp/{slot}'
                        # cn_modules_paths[device['serial']] = f'{cip_path}/{cnet_node_num}/bp/0'
                        pass
                except ResponseError:
                    pass
                    # print("Response ERROR")
            driver.close()
        except ResponseError:
            print('.', end='')
            driver.close()
    return found_controlnet_nodes, cn_modules_paths


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


def discover(entry_point):
    bp_sn, bp, cn_path = scan_bp(test_entry)
    assert type(cn_path) is dict
    if len(cn_path):
        # scan controlnet
        for cn_serial, cip_path in cn_path.items():
            cn_nodes, cn_nodes_paths = scan_cn(cip_path)
            print(cn_nodes)
            if len(cn_nodes) > 1:
                for cn_serial, cip_path in cn_nodes_paths.items():
                    bp_sn, bp, cn_path = scan_bp(cip_path)
                    print(bp_sn)
                    print(bp)
                    print(cn_path)

    else:
        print(f'Single backplane system found')
        pass



if __name__ == '__main__':
    print('Scanner lib standalone running')
    ic.disable()

    test_entry = '11.80.18.1'
    discover(test_entry)

    pass
