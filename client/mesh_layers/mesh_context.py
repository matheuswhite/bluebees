from dataclasses import dataclass


@dataclass
class HardContext:
    seq: int
    ttl: int
    is_crtl_msg: bool
    seq_zero: int
    seg_o: int
    seg_n: int
    szmic: int

    def reset(self):
        self.ttl = 3
        self.is_ctrl_msg = False
        self.seq_zero = 0
        self.seg_o = 0
        self.seg_n = 0
        self.szmic = 0


@dataclass
class SoftContext:
    src_addr: bytes
    dst_addr: str
    node_name: str
    network_name: str
    application_name: str
    is_devkey: bool
    ack_timeout: int
    segment_timeout: int
