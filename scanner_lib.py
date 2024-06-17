from collections import namedtuple

from icecream import ic

from pycomm3 import CIPDriver, Services, DataTypes
from pycomm3.exceptions import ResponseError, RequestError, CommError

from global_data import Entry_point

def scan_bp(cip_path):
    """
    Scans the specified CIP path for ControlNet modules and returns a dictionary
    mapping their serial numbers to their corresponding paths and whether they've been scanned.

    Args:
        cip_path (str): The CIP path to scan.

    Returns:
        dict: A dictionary where keys are serial numbers of ControlNet modules,
              and values are tuples containing the module's path and a boolean indicating
              whether it's been scanned.
    """
    future_scan = {}
    backplane_sn = None

    driver = CIPDriver(cip_path)
    driver.open()
    for slot in range(14):
        try:
            device = driver.get_module_info(slot)
            module_serial_number = device['serial']
            module_product_code = device['product_code']
            # print(f'{slot}: {device['product_name']}')
            print(device)

            # Check for ControlNet modules (product_code 22)
            if module_product_code == 22:
                ic(f'controlnet in slot {slot}')
                # Add to future_scan if not already present
                if module_serial_number in future_scan.keys():
                    pass
                else:
                    future_scan[module_serial_number]=(
                        f'{cip_path}/bp/{slot}/cnet',
                        False   # Initially set to False (not scanned)
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

    driver.close()
    return backplane_sn, future_scan

def scan_cn(cip_path):
        print(f'Scaning {cip_path}...')
        for cnet_node_num in range(100):
            target = f'{cip_path}/{cnet_node_num}/bp/0'
            # print(f' Scan address {cnet_node_num}')
            try:
                driver = CIPDriver(target)
                driver.open()
                for slot in range(13):
                    device = driver.get_module_info(slot)
                    if device is False or device is True:
                        continue
                    ic(device)

                    if device['product_code'] == 22:
                        print(f'ControlNet module at slot {slot}')
                        # future_scan.append(f'{entry_point}/bp/{slot}/cnet/')
                        pass
                driver.close()
            except ResponseError:
                print('.', end='')
                driver.close()


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


def check_module(driver: CIPDriver, slot: int):
        try:
            device = driver.get_module_info(slot)
            serial_number = device['serial']
            if serial_number in scanned:
                return True
            else:
                scanned.add(serial_number)
                return device

        except RequestError:
            print('.', end='')
            return False
        except ResponseError:
            pass
            # self.progress.emit("Response ERROR")
            # ic(f"No device in slot {slot}")
            return False

def check_module_by_identity(cip_path, slot):
        full_cip_path = f'{cip_path}/bp/{slot}'
        device = CIPDriver.list_identity(full_cip_path)
        return device

if __name__ == '__main__':
    # Example usage decode_serial_number
    # data = b'\x00\x08\x00\x00\x00\x00\x04\x00\x00\x00\x01\x01\xef\xa5\x1a\x00\x00'
    # decoded_serial = decode_serial_number(data)
    # print(f"Decoded Serial Number: {decoded_serial}")

    print('Scanner lib standalone running')

    test_entry = '11.80.18.1'
    bp_sn, fs = scan_bp(test_entry)
    ic(bp_sn)
    ic(fs)
    for controlnet_sn in fs.keys():
        cip_path, already_scanned = fs[controlnet_sn]
        if not already_scanned:
            scan_cn(cip_path)

    pass
