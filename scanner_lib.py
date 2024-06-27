from collections import namedtuple
from pprint import pprint
import time

from icecream import ic

ic.disable()

from pycomm3 import CIPDriver, Services, DataTypes, ClassCode, STRING
from pycomm3.exceptions import ResponseError, RequestError, CommError
from pycomm3.custom_types import ModuleIdentityObject

from pycomm3 import parse_connection_path
from pycomm3.logger import configure_default_logger

import global_data
from shassy import shassy_ident

bp_all = set([])
full_map = {}

controlnet_module = 22
flex_adapter = 37
ethernet_module = 166
plc_module = 93, 94
serial_unknown = 'FFFFFFFF'


class AlreadyScanned(Exception):
    """Custom exception to indicate a backplane has already been scanned."""

    def __init__(self, bp_serial):
        super().__init__(f"Backplane with serial {bp_serial} has already been scanned.")


class BackplaneSerialNumberMissmatch(Exception):
    """an exception occurs when the backplane serial number does not match the current serial number"""

    def __init__(self, bp_serial_current, bp_serial_prev):
        super().__init__(f"Backplane SN {bp_serial_current} != {bp_serial_prev}")


def scan_bp(cip_path, entry_point: bool = False, format='', exclude_bp_sn='', p=print):
    """
    Scans the Backplane by specified CIP path for modules and returns a dictionary
    mapping their serial numbers to their corresponding paths and whether they've been scanned.

    Args:
        :param cip_path (str): The CIP path to scan.
        :param entry_point (bool): True if bp is entry point
        :param p (func): callback for progress update




    Returns:
        dict: A dictionary where keys are serial numbers of modules,
              and values are tuples containing the module's path and a boolean indicating
              whether it's been scanned.
    """
    this_bp = {}

    modules_in_bp = {}
    modules_all = set([])
    cn_modules_paths = {}
    this_flex_response = False

    if entry_point:  # --------------------------------------------------------------------------- access to bp via eth
        p(f'Scanning entry point {cip_path}')
        backplane_size = 13
        current_slot = -1
        while current_slot <= backplane_size:
            current_slot += 1
            try:
                with CIPDriver(f'{cip_path}/bp/{current_slot}') as temporary_driver:
                    # p(temporary_driver)

                    entry_point_module = temporary_driver.generic_message(
                        service=Services.get_attributes_all,
                        class_code=0x1,
                        instance=0x1,
                        connected=False,
                        unconnected_send=True,
                        route_path=True,
                        name='Who'
                    )
                    if entry_point_module:
                        epm = ModuleIdentityObject.decode(entry_point_module.value)
                    else:
                        continue
                    if epm['product_code'] in (ethernet_module, controlnet_module, plc_module) and not this_bp:
                        # no bp info yet
                        # https://www.plctalk.net/threads/rockwell-plc-chassis-serial-number-rs-logix.86426/
                        this_bp_response = temporary_driver.generic_message(
                            service=Services.get_attributes_all,
                            class_code=0x66,
                            instance=0x1,
                            attribute=0x0,
                            data_type=shassy_ident,
                            connected=False,
                            unconnected_send=True,
                            route_path=True
                        )
                        if this_bp_response.error:
                            # BackPlane response not supported
                            pass
                        else:
                            this_bp = this_bp_response.value
                            this_bp['serial'] = f'{this_bp['serial_no']:0>8x}'
                            backplane_size = this_bp['size']
                            p(f'BackPlane:')
                            p(this_bp)
                    # store module info
                    # modules_in_bp[current_slot] = ic(epm['serial'])

            except CommError:
                print()
                raise f"Can't communicate to {cip_path}!"
    else:  # -------------------------------------------------------------------------------------- access to bp via cn
        p(f'Scanning BackPlane at {cip_path}')
        try:
            with CIPDriver(f'{cip_path}') as temporary_driver:
                # pprint(temporary_driver)
                this_module_response = temporary_driver.generic_message(
                    service=Services.get_attributes_all,
                    class_code=0x1,
                    instance=0x1,
                    connected=False,
                    unconnected_send=True,
                    route_path=True,
                    name='Who'
                )
                if this_module_response:
                    this_module = ModuleIdentityObject.decode(this_module_response.value)
                else:
                    raise CommError(f"Can't complete WHO request to {cip_path}")

                if this_module['product_code'] in (controlnet_module,):
                    this_bp_response = temporary_driver.generic_message(
                        service=Services.get_attributes_all,
                        class_code=0x66,
                        instance=0x1,
                        attribute=0x0,
                        data_type=shassy_ident,
                        connected=False,
                        unconnected_send=True,
                        route_path=True
                    )
                    if this_bp_response.error:
                        # BackPlane response not supported
                        pass
                    else:
                        this_bp = this_bp_response.value
                        this_bp['serial'] = f'{this_bp['serial_no']:0>8x}'
                        # global_data.bp[this_bp['serial']] = {
                        #     'bp': this_bp,
                        # }

                if this_module['product_code'] in (flex_adapter,):
                    this_flex_response = temporary_driver.generic_message(
                        service=Services.get_attributes_all,
                        class_code=0x78,
                        instance=0x01,
                        # attribute=0x0,
                        connected=True,
                        unconnected_send=True,
                        route_path=True,
                        name="flex_modules_info",
                    )
                    p(f'{format}Flex adapter at {cip_path}')
                    # pprint(this_flex_response.value)
        except CommError:
            print()
            raise CommError(f"Can't communicate to {cip_path}!")

    if not this_bp or this_flex_response:
        return this_flex_response.value

    this_bp_sn = this_bp['serial']
    global_data.bp[this_bp_sn] = {
        'bp': this_bp,
    }

    for slot in range(this_bp['size']):
        try:
            this_module_path = f'{cip_path}/bp/{slot}'
            driver = CIPDriver(this_module_path)
            driver.open()

            this_module_response = driver.generic_message(
                service=Services.get_attributes_all,
                class_code=0x1,
                instance=0x1,
                connected=False,
                unconnected_send=True,
                route_path=True,
                name='Who'
            )
            # driver.close()
            if this_module_response:
                this_module = ModuleIdentityObject.decode(this_module_response.value)
                p(f"{format}Slot {slot:02} = [{this_module['serial']}] {this_module['product_name']}")
                modules_in_bp[slot] = ic(this_module['serial'])

            else:
                p(f'{format}Slot {slot:02} = EMPTY')
                modules_in_bp[slot] = None

                continue

            module_serial_number = this_module['serial']
            modules_all.add(module_serial_number)
            module_product_code = this_module['product_code']

            if module_product_code == controlnet_module:
                # p(f'+  <-- (controlnet in slot {slot})')  # moved down
                if entry_point:
                    p(f'+  <-- (controlnet module in slot {slot}. The way to access ControlNet)')
                    #  only CN modules in entry point's backplane will be scanned in future
                    #  this is the main limitation
                    cn_modules_paths[module_serial_number] = f'{cip_path}/bp/{slot}/cnet'

            # Requests the name of the program running in the PLC. Uses KB `23341`_ for implementation.
            if module_product_code in plc_module:
                try:
                    response = driver.generic_message(
                        service=Services.get_attributes_all,
                        class_code=ClassCode.program_name,
                        instance=1,
                        data_type=STRING,
                        name="get_plc_name",
                    )
                    if not response:
                        raise ResponseError(f"response did not return valid data - {response.error}")

                    this_module["name"] = response.value
                    p(f'+  <-- {response.value}')
                except Exception as err:
                    pass
                    # this_module["name"] = None

        except ResponseError:
            p(f'{format} !!! Module in slot {slot} may be broken')
            modules_in_bp[slot] = None
            continue
        except CommError:
            p(f'{format} !!! Module in slot {slot} may be broken')
            modules_in_bp[slot] = None
            continue
        global_data.module[this_module['serial']] = this_module
        driver.close()

    global_data.bp[this_bp_sn].update(modules_in_bp)

    return this_bp_sn, modules_in_bp, this_bp, cn_modules_paths


def scan_cn(cip_path, format='', exclude_bp_sn='', p=print, current_cn_node_update=None):
    if current_cn_node_update:
        cn_node_updt = current_cn_node_update
    else:
        def cn_node_updt(*args, **kwargs):
            pass

    cn_modules_paths = {}
    found_controlnet_nodes = []
    p(f'Scanning ControlNet {cip_path}...')
    for cnet_node_num in range(100):
        target = f'{cip_path}/{cnet_node_num}'
        cn_node_updt(f'{cnet_node_num:02}')
        # time.sleep(0.02)

        # print(f' Scan address {cnet_node_num}')
        try:
            driver = CIPDriver(target)
            driver.open()
            cn_module = driver.generic_message(
                service=Services.get_attributes_all,
                class_code=0x1,
                instance=0x1,
                # attribute=0x0,
                # data_type=shassy_ident,
                connected=False,
                unconnected_send=True,
                route_path=True,
                name='Who'
            )
            if cn_module.error:
                # no module. CN address not in use
                # print('.', end='')
                pass
            else:
                p(f'{format} found node [{cnet_node_num:02}]')
                m = ModuleIdentityObject.decode(cn_module.value)
                # p(m)
                found_controlnet_nodes.append(cnet_node_num)
                cn_modules_paths[m['serial']] = target
            driver.close()
        except ResponseError:
            # print('.', end='')
            driver.close()
    cn_node_updt('--')
    # print('-'*20)
    # pprint(cn_modules_paths)
    return found_controlnet_nodes, cn_modules_paths


def discover(entry_point):
    import pprint
    p = pprint.pprint
    ep = scan_bp(test_entry, entry_point=True)
    bp_sn, modules, bp, cn_path = ep
    assert type(cn_path) is dict
    if len(cn_path):
        # scan controlnet
        for cn_serial, cip_path in cn_path.items():
            cn_nodes, cn_nodes_paths = scan_cn(cip_path)
            print(cn_nodes)
            if len(cn_nodes) > 1:
                for cn_serial, cip_path in cn_nodes_paths.items():
                    try:
                        bp = scan_bp(cip_path)
                    except ValueError:
                        pass
                    p(bp)

    else:
        print(f'Single backplane system found')
        pass


if __name__ == '__main__':
    print('Scanner lib standalone running')
    ic.enable()
    # configure_default_logger(filename='/home/damir/pycomm3.log')

    test_entry = '192.168.0.123'
    discover(test_entry)

    pass
