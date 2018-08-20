#!/usr/bin/python3
from core.utils import borg
from platform import system


@borg
class GlobalSetting:

    def __init__(self):
        self.dongle_address = ''
        self.dongle_baudrate = 115200
        self.dongle_max_read_size = 66
        self.dongle_pb_adv = 1
        self.dongle_pb_gatt = 2
        self.dongle_current_pb = self.dongle_pb_adv

        self.adv_link_close_success = b'\x00'
        self.adv_link_close_timeout = b'\x01'
        self.adv_link_close_fail = b'\x02'
        self.adv_link_timeout_value = 30.0
        self.adv_max_link_id = 0xFFFFFFFF
        self.adv_link_open = b'\x00'
        self.adv_link_ack = b'\x01'
        self.adv_link_close = b'\x02'
        self.adv_pbc_type_mask = b'\x03'
        self.adv_bearer_opcode_mask = b'\xFC'

        self.gprov_min_delay = 0.020
        self.gprov_max_delay = 0.050


@borg
class PbAdvSettings:

    def __init__(self):
        self.mtu_max_size = 24


@borg
class AdvSettings:

    def __init__(self):
        if system() == 'Linux':
            self.port = '/dev/ttyACM0'
        elif system() == 'Windows':
            self.port = 'COM3'
        # Mac
        elif system() == 'Darwin':
            self.port = ''
        else:
            self.port = ''
        self.baud_rate = 115200
