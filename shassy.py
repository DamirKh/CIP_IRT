from pycomm3 import Struct, DINT, STRING, REAL, SINT, INT, UDINT, USINT, UINT

shassy_ident = Struct(
    USINT('rx_bad_m_crc_ctr'),
    USINT('multicast_crc_error_threshold'),
    USINT('rx_bad_crc_ctr'),
    USINT('rx_bus_timout_ctr'),
    USINT('tx_bad_crc_ctr'),
    USINT('tx_bus_timeout_ctr'),
    USINT('tx_retry_limit'),
    USINT('bp_status'),
    UINT('mod_addr'),
    USINT('major_rev'),
    USINT('minor_rev'),
    UDINT('serial_no'),
    # DINT('serial_no'),
    UINT('size')
)

