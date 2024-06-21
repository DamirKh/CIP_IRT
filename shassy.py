from pycomm3 import Struct, DINT, STRING, REAL, SINT, INT, UDINT

shassy_ident = Struct(
    SINT('rx_bad_m_crc_ctr'),
    SINT('multicast_crc_error_threshold'),
    SINT('rx_bad_crc_ctr'),
    SINT('rx_bus_timout_ctr'),
    SINT('tx_bad_crc_cnr'),
    SINT('tx_bus_timeout_ctr'),
    SINT('tx_retry_limit'),
    SINT('bp_status'),
    INT('mod_addr'),
    SINT('major_rev'),
    SINT('minor_rev'),
    UDINT('serial_no'),
    # DINT('serial_no'),
    INT('size')
)

