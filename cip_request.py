from pycomm3 import Services, ClassCode, STRING
from shassy import shassy_ident

who = {
    "service": Services.get_attributes_all,
    "class_code": 0x1,
    "instance": 0x1,
    "connected": False,
    "unconnected_send": True,
    "route_path": True,
    "name": 'Who'
}

who_connected = {
    "service": Services.get_attributes_all,
    "class_code": 0x1,
    "instance": 0x1,
    "connected": True,
    "unconnected_send": False,
    "route_path": True,
    "name": 'Who'
}

bp_info = {
    "service": Services.get_attributes_all,
    "class_code": 0x66,
    "instance": 0x1,
    "attribute": 0x0,
    "data_type": shassy_ident,
    "connected": False,
    "unconnected_send": True,
    "route_path": True
}

flex_info = {
    "service": Services.get_attributes_all,
    "class_code": 0x78,
    "instance": 0x01,
    # "attribute":0x0,
    "connected": True,
    "unconnected_send": True,
    "route_path": True,
    "name": "flex_modules_info",
}

plc_name = {
    "service": Services.get_attributes_all,
    "class_code": ClassCode.program_name,
    "instance": 1,
    "data_type": STRING,
    "connected": False,
    "unconnected_send": True,
    "route_path": True,
    "name": "get_plc_name",
}
