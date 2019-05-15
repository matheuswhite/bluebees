from core.utils import crc8
from core.log import Log, LogLevel

MAX_MTU = 20 - 5

log = Log('Transaction')
log.level = LogLevel.Wrn.value


class Transaction:

    def __init__(self, content=b''):
        self.content = content
        self.all_segments = {}
        self.recv_medata = {
            'n_segments': 0,
            'total_length': 0,
            'fcs': 0,
        }

    def segments(self):
        index = 0
        while len(self.content) > 0:
            if index == 0:
                seg_n = int(len(self.content)/MAX_MTU)
                first_byte = int(seg_n << 2).to_bytes(1, 'big')
                total_length = len(self.content).to_bytes(2, 'big')
                fcs = crc8(self.content).to_bytes(1, 'big')
                payload = self.content[0:MAX_MTU]
                segment = first_byte + total_length + fcs + payload

                yield segment
            else:
                first_byte = int((index << 2) | 0x02).to_bytes(1, 'big')
                payload = self.content[0:MAX_MTU]
                segment = first_byte + payload

                yield segment
            index += 1
            self.content = self.content[MAX_MTU:]

    def add_recv_segment(self, segment: bytes):
        op_code = segment[0] & 0x03
        if op_code == 0x00:
            self.recv_medata['n_segments'] = segment[0] >> 2
            self.recv_medata['total_length'] = int.from_bytes(segment[1:3], 'big')
            self.recv_medata['fcs'] = segment[3]
            self.all_segments[0] = segment[4:]
        elif op_code == 0x02:
            index = segment[0] >> 2
            self.all_segments[index] = segment[1:]

    def get_recv_transaction(self):
        try:
            payload = b''
            for x in range(self.recv_medata['n_segments']+1):
                payload += self.all_segments[x]
                log.dbg(f'Payload: {payload}')

            if len(payload) != self.recv_medata['total_length']:
                return None, 'length_wrong'

            fcs_calc = crc8(payload)
            if fcs_calc != self.recv_medata['fcs']:
                return None, 'fcs_wrong'

            return payload, 'none'
        except KeyError:
            return None, 'n_segments_wrong'
