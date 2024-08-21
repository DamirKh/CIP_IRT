from pprint import pprint

from icecream import ic

from pycomm3 import CIPDriver, Tag
from pycomm3.exceptions import ResponseError, RequestError, CommError

from pycomm3.logger import configure_default_logger

import tool
from global_data import global_data, new_blank_module

from shassy import MyModuleIdentityObject
import cip_request
import serial_generator

bp_all = set([])
full_map = {}
modules_all = set([])

controlnet_module = 22, 7
flex_adapter = 37
ethernet_module = 166
plc_module = 93, 94
serial_unknown = serial_generator.SerialGenerator()

long_path_error_values = b'\x18\x03\x01\x00', b'\x18\x03\x02\x00'  # empiric way


class AlreadyScanned(Exception):
    """Custom exception to indicate a backplane has already been scanned."""

    def __init__(self, serial):
        super().__init__(f"Module with serial {serial} has already been scanned.")

class ModuleUnavailable(Exception):
    """Custom exception to indicate module unavailable."""

    def __init__(self, path):
        super().__init__(f"Module {path} unavailable")


class BackplaneSerialNumberMissmatch(Exception):
    """an exception occurs when the backplane serial number does not match the current serial number"""

    def __init__(self, bp_serial_current, bp_serial_prev):
        super().__init__(f"Backplane SN {bp_serial_current} != {bp_serial_prev}")


def get_module_sn(cip_path):
    driver: CIPDriver = CIPDriver(cip_path)
    driver.open()
    module_response = driver.generic_message(**cip_request.who)
    if module_response.error:  # and module_response.value in long_path_error_values:
        module_response = driver.generic_message(**cip_request.who_connected)
        if module_response.error:
            # raise ModuleUnavailable(cip_path)
            return None
    module = MyModuleIdentityObject.decode(module_response.value)
    return module["serial"]

def get_backplane_sn(cip_path):
    driver: CIPDriver = CIPDriver(cip_path)
    driver.open()
    bp_response = driver.generic_message(**cip_request.bp_info)
    if bp_response.error:  # let's try another way
        bp_response = driver.generic_message(**cip_request.bp_info_connected)
        if bp_response.error:
            # raise ModuleUnavailable(cip_path)
            return None
    bp = bp_response.value
    serial = f'{bp['serial_no']:0>8x}'
    return serial


def path_left_strip(path: str) -> str:
    """
    10/20/30  --> 20/30
    """
    _path = path.split('/')[1:]
    if not len(_path):
        return '/'
    else:
        return f"/{'/'.join(_path)}"


def scan_bp(cip_path, module_found=pprint):

    modules_in_bp = {}
    cn_modules_paths = {}
    this_flex_response = False

    with CIPDriver(cip_path) as entry_point_module_driver:
        # p(entry_point_module_driver)

        entry_point_module = entry_point_module_driver.generic_message(**cip_request.who)
        epm = MyModuleIdentityObject.decode(entry_point_module.value)

        this_bp_response = entry_point_module_driver.generic_message(**cip_request.bp_info)
        bp_as_module = new_blank_module()

        if this_bp_response.error:
            # BackPlane response not supported
            print(f"Can't get backplane info via {cip_path}: ({epm['product_type']} {epm['product_name']})")
            # this_bp['serial'] = str(serial_unknown)
            pass
        else:
            this_bp = this_bp_response.value

            bp_as_module["serial"] = f'{this_bp['serial_no']:0>8x}'
            bp_as_module["size"] = this_bp.get('size', None)
            bp_as_module["rev"] = f"{this_bp.get('major_rev', 0)}.{this_bp.get('minor_rev', 0)}"
            bp_as_module["major"] = this_bp.get('major_rev', 0)
            bp_as_module["minor"] = this_bp.get('minor_rev', 0)
            bp_as_module["product_name"] = "Backplane"
            bp_as_module["product_type"] = f"{this_bp.get('size', "UNKNOWN")} slots"
            # bp_as_module["path"] = f"{cip_path}/bp"
            _path = path_left_strip(cip_path)
            if _path[-1] == '/':
                bp_as_module["path"] = f"{path_left_strip(cip_path)}bp"
            else:
                bp_as_module["path"] = f"{path_left_strip(cip_path)}/bp"
            module_found(bp_as_module)
        bp_known_size = True if bp_as_module["size"] else False

        print(f'BackPlane: {this_bp}')

# ########

    if not bp_known_size:
        backplane_size = 100
    else:
        backplane_size = bp_as_module["size"]
    current_slot = -1
    while current_slot <= backplane_size:
        current_slot += 1
        _path = f'{path_left_strip(cip_path)}/bp/{current_slot}'
        if current_slot == epm['mod_addr']:
            module_found(epm)
        try:
                # with CIPDriver(f'{cip_path}/bp/{current_slot}') as entry_point_module_driver:
                #     # p(entry_point_module_driver)
                #
                #     entry_point_module = entry_point_module_driver.generic_message(**cip_request.who)
                #     if entry_point_module:
                #         epm = MyModuleIdentityObject.decode(entry_point_module.value)
                #     else:
                #         continue
                #     if not this_bp:
                #         # if epm['product_code'] in (ethernet_module, controlnet_module, plc_module) and not this_bp:
                #         # no bp info yet
                #         # https://www.plctalk.net/threads/rockwell-plc-chassis-serial-number-rs-logix.86426/
                #         this_bp_response = entry_point_module_driver.generic_message(**cip_request.bp_info)
                #         if this_bp_response.error:
                #             # BackPlane response not supported
                #             p(f"Can't get backplane info via {cip_path}/bp/{current_slot}")
                #             # this_bp['serial'] = str(serial_unknown)
                #             pass
                #         else:
                #             this_bp = this_bp_response.value
                #             this_bp['serial'] = f'{this_bp['serial_no']:0>8x}'
                #             backplane_size = this_bp.get('size', 20)
                #             p(f'BackPlane:')
                #             p(this_bp)
                #     # store module info
                #     # modules_in_bp[current_slot] = ic(epm['serial'])

            except CommError:
                raise CommError(f"Can't communicate to {cip_path}!")
    # -------------------------------------------------------------------------------------- access to bp via cn
    else:
        p(f'Scanning BackPlane at {cip_path}')
        try:
            with CIPDriver(f'{cip_path}') as entry_point_module_driver:
                # pprint(entry_point_module_driver)
                this_module_response: Tag = entry_point_module_driver.generic_message(**cip_request.who)
                if this_module_response:
                    this_module = MyModuleIdentityObject.decode(this_module_response.value)
                else:
                    raise CommError(f"Can't complete WHO request to {cip_path}")

                # here we've got controlnet module by full cip path via controlnet
                if this_module['product_code'] in controlnet_module:
                    this_bp_response = entry_point_module_driver.generic_message(**cip_request.bp_info)
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
                    this_flex_response = entry_point_module_driver.generic_message(**cip_request.flex_info)
                    p(f'{format}Flex adapter at {cip_path}')
                    pprint(this_flex_response.value)
                    # b'\x01\x00\x11\x02\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f'  # 2 modules
                    # b'\x01\x00\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f'  # IB32 module
                    # b'\x11\x02\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f\x00\x0f'  # OB32 module
        except CommError:
            print()
            raise CommError(f"Can't communicate to {cip_path}!")
        except AlreadyScanned:
            pass

    if this_flex_response:  # TODO
        global_data.cn_flex[this_module['serial']] = {
            'adapter': this_module,
            'modules': this_flex_response.value
        }
        return this_module

    this_bp['serial'] = this_bp.get('serial', str(serial_unknown))  # do nothing if bp serial set
    this_bp_sn = this_bp.get('serial')
    global_data.bp[this_bp_sn] = {
        'bp': this_bp,
    }
    p('Backpane')
    p(this_bp)

    # bp_as_module = new_blank_module()
    # bp_as_module["serial"] = this_bp_sn
    # bp_as_module["size"] = this_bp.get('size', None)
    # bp_as_module["rev"] = f"{this_bp.get('major_rev', 0)}.{this_bp.get('minor_rev', 0)}"
    # bp_as_module["major"] = this_bp.get('major_rev', 0)
    # bp_as_module["minor"] = this_bp.get('minor_rev', 0)
    # bp_as_module["product_name"] = "Backplane"
    # bp_as_module["product_type"] = f"{this_bp.get('size', "UNKNOWN")} slots"
    # # bp_as_module["path"] = f"{cip_path}/bp"
    # _path = path_left_strip(cip_path)
    # if _path[-1] == '/':
    #     bp_as_module["path"] = f"{path_left_strip(cip_path)}bp"
    # else:
    #     bp_as_module["path"] = f"{path_left_strip(cip_path)}/bp"
    #
    #
    # module_found(bp_as_module)
    # bp_known_size = True if bp_as_module["size"] else False

    for slot in range(this_bp.get('size', 14)):
        _communication_module_here = False
        if cip_path == '192.168.0.124/bp/2/cnet/8/': # and slot == 2:  # Exam: '192.168.0.124/bp/2/cnet/3'  '192.168.0.124'  '192.168.0.124/bp/2/cnet/3' 192.168.0.124/bp/2/cnet/1/bp/9
            pass  # trap for debug. edit string above and set breakpoint here
        try:
            _long_path = this_module_path = f'{cip_path}/bp/{slot}'
            driver: CIPDriver = CIPDriver(this_module_path)
            driver.open()

            this_module_response = driver.generic_message(**cip_request.who)
            if this_module_response.error and this_module_response.value in long_path_error_values:
                # some communication modules does not respond to message via long path with bp
                _communication_module_here = cip_path.split('/')[-1]
                driver.close()
                try:
                    this_module_path: str = f'{cip_path}'  # strip /bp/{slot} part
                    driver: CIPDriver = CIPDriver(this_module_path)
                    driver.open()

                    this_module_response = driver.generic_message(**cip_request.who_connected)
                except ResponseError:
                    pass  # no way
                except CommError:
                    pass  # nothing to do
                pass

            if this_module_response:  # this block executed for every real module ######################################
                this_module = MyModuleIdentityObject.decode(this_module_response.value)

                # if this_module["serial"] in modules_all:  # Check for communication loop
                #     raise AlreadyScanned(this_module["serial"])
                # else:
                #     modules_all.add(this_module["serial"])

                # _path = _long_path.split('/')[1:]
                this_module["path"] = path_left_strip(_long_path)
                this_module["slot"] = slot
                this_module["product_name"] = tool.remove_control_chars(this_module["product_name"])
                if _communication_module_here:
                    this_module['cn_node'] = _communication_module_here
                if this_module['product_code'] in controlnet_module:
                    this_module_node_address_response = driver.generic_message(**cip_request.cn_address)
                    if this_module_node_address_response:
                        this_module_node_address = this_module_node_address_response.value['cn_node_number1']
                        this_module['cn_node'] = this_module_node_address
                    else:
                        this_module['cn_node'] = cip_path.split('/')[-1]
                p(f"{format}Slot {slot:02} = [{this_module['serial']}] {this_module['product_name']}")
                modules_in_bp[slot] = ic(this_module['serial'])
                if module_found:
                    module_found(this_module)

            else:
                if bp_known_size:
                    p(f'{format}Slot {slot:02} = EMPTY')
                    modules_in_bp[slot] = None
                    empty_slot_as_module = new_blank_module()
                    empty_slot_as_module["slot"] = slot
                    empty_slot_as_module["product_name"] = "Empty slot"
                    # empty_slot_as_module["serial"] = f'{this_bp_sn}-{slot:0>2}'
                    empty_slot_as_module["path"] = path_left_strip(_long_path)

                    module_found(empty_slot_as_module)
                else:
                    #bp size unknown
                    pass

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
                    response: Tag = driver.generic_message(**cip_request.plc_name)
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
        except AlreadyScanned:
            break
        # global_data.module[this_module['serial']] = this_module
        driver.close()

    # global_data.bp[this_bp_sn].update(modules_in_bp)

    return this_bp_sn, modules_in_bp, this_bp, cn_modules_paths


def scan_cn(cip_path, format='', exclude_bp_sn='', p=print, current_cn_node_update=None, max_node_num=100):
    if current_cn_node_update:  # ---------------------------------------------logging function
        cn_node_updt = current_cn_node_update
    else:  # ---------------------------------------------------------------NO logging function
        def cn_node_updt(*args, **kwargs):
            pass

    cn_modules_paths = {}
    found_controlnet_nodes = []
    p(f'Scanning ControlNet {cip_path}...')
    for cnet_node_num in range(max_node_num + 1):  # 100 for production
        target = f'{cip_path}/{cnet_node_num}'
        cn_node_updt(f'{cnet_node_num:02}')
        # time.sleep(0.02)

        # print(f' Scan address {cnet_node_num}')
        try:
            driver = CIPDriver(target)
            driver.open()
            cn_module = driver.generic_message(**cip_request.who)
            if cn_module.error:
                # no module. CN address not in use
                # print('.', end='')
                pass
            else:
                p(f'{format} found node [{cnet_node_num:02}]')
                m = MyModuleIdentityObject.decode(cn_module.value)
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
