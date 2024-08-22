from io import BytesIO

from pycomm3 import (Struct,
                     DINT,
                     STRING,
                     REAL,
                     SINT,
                     INT,
                     UDINT,
                     USINT,
                     UINT,
                     SHORT_STRING,
                     n_bytes,
                     # PRODUCT_TYPES,  # defines below
                     VENDORS
                     )
# Updated datas from picomm3/cip/status_info.py
_PRODUCT_TYPES = {
    0x00: "Generic Device (deprecated)",
    0x02: "AC Drive",
    0x03: "Motor Overload",
    0x04: "Limit Switch",
    0x05: "Inductive Proximity Switch",
    0x06: "Photoelectric Sensor",
    0x07: "General Purpose Discrete I/O",
    0x09: "Resolver",
    0x0A: "General Purpose Analog I/O",
    0x0C: "Communications Adapter",
    0x0E: "Programmable Logic Controller",
    0x10: "Position Controller",
    0x13: "DC Drive",
    0x15: "Contactor",
    0x16: "Motor Starter",
    0x17: "Soft Start",
    0x18: "Human-Machine Interface",
    0x1A: "Mass Flow Controller",
    0x1B: "Pneumatic Valve",
    0x1C: "Vacuum Pressure Gauge",
    0x1D: "Process Control Value",
    0x1E: "Residual Gas Analyzer",
    0x1F: "DC Power Generator",
    0x20: "RF Power Generator",
    0x21: "Turbomolecular Vacuum Pump",
    0x22: "Encoder",
    0x23: "Safety Discrete I/O Device",
    0x24: "Fluid Flow Controller",
    0x25: "CIP Motion Drive",
    0x26: "CompoNet Repeater",
    0x27: "Mass Flow Controller, Enhanced",
    0x28: "CIP Modbus Device",
    0x29: "CIP Modbus Translator",
    0x2A: "Safety Analog I/O Device",
    0x2B: "Generic Device (keyable)",
    0x2C: "Managed Switch",
    0x2D: "CIP Motion Safety Drive Device",
    0x2E: "Safety Drive Device",
    0x2F: "CIP Motion Encoder",
    0x31: "CIP Motion I/O",
    0x32: "ControlNet Physical Layer Component",
    0xC8: "Embedded Component",
}


PRODUCT_TYPES = {
    **_PRODUCT_TYPES,
    **{v: k for k, v in _PRODUCT_TYPES.items()},
}

shassy_ident = Struct(
    USINT('rx_bad_m_crc_ctr'),
    USINT('multicast_crc_error_threshold'),
    USINT('rx_bad_crc_ctr'),
    USINT('rx_bus_timout_ctr'),
    USINT('tx_bad_crc_ctr'),
    USINT('tx_bus_timeout_ctr'),
    USINT('tx_retry_limit'),
    USINT('bp_status'),
    UINT('mod_addr'),  #  module's slot number in shassy
    USINT('major_rev'),
    USINT('minor_rev'),
    UDINT('serial_no'),
    # DINT('serial_no'),
    UINT('size')
)

My_Module_Ident = Struct(
    UINT("vendor#"),
    UINT("product_type#"),
    UINT("product_code#"),
    USINT("major"),
    USINT("minor"),
    n_bytes(2, "status"),
    UDINT("serial"),
    SHORT_STRING("product_name"),
)

My_CN_Node_number = Struct(
    USINT('cn_node_number1'),
    USINT('cn_node_number2'),
    USINT('UNKNOWN1'),
    USINT('UNKNOWN2'),
)


class MyModuleIdentityObject(
    Struct(
        UINT("vendor#"),
        UINT("product_type#"),
        UINT("product_code"),
        USINT("major"),
        USINT("minor"),
        n_bytes(2, "status"),
        UDINT("serial"),
        SHORT_STRING("product_name"),
    )
):
    @classmethod
    def _decode(cls, stream: BytesIO):
        values = super(MyModuleIdentityObject, cls)._decode(stream)
        values["product_type"] = PRODUCT_TYPES.get(values["product_type#"], "UNKNOWN")
        values["vendor"] = VENDORS.get(values["vendor#"], "UNKNOWN")
        values["serial"] = f"{values['serial']:08x}"
        values["rev"]=f'{values["major"]}.{values["minor"]}'

        return values
