from collections import namedtuple
from pprint import pprint
import time

from icecream import ic

ic.disable()

from pycomm3 import CIPDriver, Services, DataTypes, ClassCode, STRING, Tag
from pycomm3.exceptions import ResponseError, RequestError, CommError
from pycomm3.custom_types import ModuleIdentityObject

from pycomm3 import parse_connection_path
from pycomm3.logger import configure_default_logger

from global_data import global_data

from shassy import shassy_ident
import serial_generator

bp_all = set([])
full_map = {}

controlnet_module = 22, 7
flex_adapter = 37
ethernet_module = 166
plc_module = 93, 94
serial_unknown = serial_generator.SerialGenerator()


class AlreadyScanned(Exception):
    """Custom exception to indicate a backplane has already been scanned."""

    def __init__(self, bp_serial):
        super().__init__(f"Backplane with serial {bp_serial} has already been scanned.")


class BackplaneSerialNumberMissmatch(Exception):
    """an exception occurs when the backplane serial number does not match the current serial number"""

    def __init__(self, bp_serial_current, bp_serial_prev):
        super().__init__(f"Backplane SN {bp_serial_current} != {bp_serial_prev}")


def scan_bp(cip_path, entry_point: bool = False, format: str = '', exclude_bp_sn='', p=print):
    """
    Scans the Backplane by specified CIP path for modules and returns a dictionary
    mapping their serial numbers to their corresponding paths and whether they've been scanned.

    apdate datas in global_data module

    Args:
        :param format (str): this string will be added before every log message
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

    # ------------------------------------------------------------------------------------- access to bp via eth
    if entry_point:
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
                    if not this_bp:
                        # if epm['product_code'] in (ethernet_module, controlnet_module, plc_module) and not this_bp:
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
                            p(f"Can't get backplane info via {cip_path}/bp/{current_slot}")
                            this_bp['serial'] = str(serial_unknown)
                            pass
                        else:
                            this_bp = this_bp_response.value
                            this_bp['serial'] = f'{this_bp['serial_no']:0>8x}'
                            backplane_size = this_bp.get('size', 20)
                            p(f'BackPlane:')
                            p(this_bp)
                    # store module info
                    # modules_in_bp[current_slot] = ic(epm['serial'])

            except CommError:
                raise CommError(f"Can't communicate to {cip_path}!")
    # -------------------------------------------------------------------------------------- access to bp via cn
    else:
        p(f'Scanning BackPlane at {cip_path}')
        try:
            with CIPDriver(f'{cip_path}') as temporary_driver:
                # pprint(temporary_driver)
                this_module_response: Tag = temporary_driver.generic_message(
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

                # here we've got controlnet module by full cip path via controlnet
                if this_module['product_code'] in controlnet_module:
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
                        # BackPlane response not supported. May be an old CN module o BP
                        # need to generate some ID for  backplane
                        # this_bp['serial'] = str(serial_unknown)

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
                    pprint(this_flex_response.value)
                    # b'\x01\x00\x11\x02\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f'  # 2 modules
                    # b'\x01\x00\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f'  # IB32 module
                    # b'\x11\x02\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f'  # OB32 module
        except CommError:
            print()
            raise CommError(f"Can't communicate to {cip_path}!")

    if this_flex_response:
        global_data.cn_flex[this_module['serial']] = {
            'adapter': this_module,
            'modules': this_flex_response.value
        }
        return this_module

    this_bp['serial'] = this_bp.get('serial', str(serial_unknown))  # do nothing if bp serial set
    this_bp_sn = this_bp.get('serial', str(serial_unknown))  # may be overkill for unknown serial
    global_data.bp[this_bp_sn] = {
        'bp': this_bp,
    }
    p('Backpane')
    p(this_bp)

    for slot in range(this_bp.get('size', 14)):
        if cip_path == '11.100.40.1/bp/3/cnet/2' and slot == 0:
            pass  # trap for debug. edit string above and set breakpoint here
        try:
            this_module_path: str = f'{cip_path}/bp/{slot}'
            driver: CIPDriver = CIPDriver(this_module_path)
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
            if this_module_response.error and this_module_response.value == b'\x18\x03\x01\x00':  # empiric way
                # some CN modules does not respond to message via long path with bp
                driver.close()
                try:
                    this_module_path: str = f'{cip_path}'  # strip /bp/{slot} part
                    driver: CIPDriver = CIPDriver(this_module_path)
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
                except ResponseError:
                    pass  # no way
                except CommError:
                    pass  # nothing to do
                pass

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

            if module_product_code in controlnet_module:
                if entry_point:
                    p(f'+  <-- (controlnet module in slot {slot}. The way to access ControlNet)')
                    #  only CN modules in entry point's backplane will be scanned in future
                    #  this is the main limitation
                    cn_modules_paths[module_serial_number] = f'{cip_path}/bp/{slot}/cnet'

            # Requests the name of the program running in the PLC. Uses KB `23341`_ for implementation.
            if this_module['product_type'] == "Programmable Logic Controller":
                try:
                    response: Tag = driver.generic_message(
                        service=Services.get_attributes_all,
                        class_code=ClassCode.program_name,
                        instance=1,
                        data_type=STRING,
                        connected=False,
                        unconnected_send=True,
                        route_path=True,
                        name="get_plc_name",
                    )
                    if not response:
                        raise ResponseError(f"response did not return valid data - {response.error}")

                    this_module["name"] = response.value
                    if not len(response.value):
                        p(f'+  <-- program not loaded')
                    else:
                        p(f'+  <-- program: {response.value}')
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
    if current_cn_node_update:  # ---------------------------------------------logging function
        cn_node_updt = current_cn_node_update
    else:  # ----------------------------------------------------------------NO logging funtion
        def cn_node_updt(*args, **kwargs):
            pass

    cn_modules_paths = {}
    found_controlnet_nodes = []
    p(f'Scanning ControlNet {cip_path}...')
    for cnet_node_num in range(10):  # 100 for production
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
    configure_default_logger(filename='/home/damir/pycomm3.log')

    test_entry = '192.168.0.123'
    discover(test_entry)

    pass
