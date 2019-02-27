from client.address import MeshAddress
from client.network_layer import NetworkLayer, NetworkPDUInfo
from signalslot.signal import Signal
from typing import List
from client.crypto import CRYPTO
from model.mesh_manager import mesh_manager
from core.scheduling import Task
from time import time
from model.network import Network


class TransportPDUInfo:

    def __init__(self, src_addr: MeshAddress, dst_addr: MeshAddress, network_name: str, application_name: str):
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.network_name = network_name
        self.application_name = application_name
        self.IN_seq_zero: int = None
        self.IN_block_ack: bytes = None
        self.IN_seg_o: int = None
        self.IN_seg_n: int = None
        self.IN_szmic: int = None
        self.IN_seq: bytes = None


# TODO Check if seq number is incresed after each send message
# TODO Drop any message that contains seq number invalid
# TODO Check byte order of this layer (big or little)
class UpperTransportLayer:

    def __init__(self, network_layer: NetworkLayer, default_ttl=3):
        self.network_layer = network_layer
        self.network_layer.new_message_signal.connect(self._handle_recv_pdu)

        self.new_message_signal = Signal(args=['transport_pdu_info', 'pdu'])
        self.seq = 0
        self.ttl = default_ttl
        self.ack_response_time = 5 # seconds
        self.application_lookup_table = {}

        self.ack_info = None
        self.ack_start_time = 0
        self.ack_elapsed_time = 0

        self.giveup_timeout = 0
        self.giveup_elapsed_time = 0
        self.giveup_start_time = 0

        self.segments_recv = {}
        self.last_segments_sent = {}
        self.segment_is_acked: bool = False

# Receive Section
    @staticmethod
    def _get_control_header(transport_pdu: bytes) -> (int, int, int):
        return transport_pdu[0] & 0x80, transport_pdu[0] & 0x7f, transport_pdu[1] & 0x80

    @staticmethod
    def _decode_seq_zero(transport_pdu: bytes) -> int:
        return int.from_bytes(transport_pdu[1:3], 'big') & 0x7ffc

    @staticmethod
    def _decode_block_ack(transport_pdu: bytes) -> bytes:
        return transport_pdu[3:7]

    @staticmethod
    def _is_segmented(transport_pdu: bytes) -> bool:
        return transport_pdu[0] & 0x80 == 1

    @staticmethod
    def _decode_szmic(transport_pdu: bytes) -> int:
        return transport_pdu[1] & 0x80

    @staticmethod
    def _decode_seg_o(transport_pdu: bytes) -> int:
        return int.from_bytes(transport_pdu[2:4], 'big') & 0x03e0

    @staticmethod
    def _decode_seg_n(transport_pdu: bytes) -> int:
        return transport_pdu[3] & 0x1f

    @staticmethod
    def _decode_segment(transport_pdu: bytes) -> bytes:
        return transport_pdu[4:]

    @staticmethod
    def _check_missed_acks(transport_pdu_info: TransportPDUInfo):
        block_ack = transport_pdu_info.IN_block_ack
        for x in range(transport_pdu_info.IN_seg_n + 1):
            ack_bit = block_ack & 0x01
            if ack_bit == 1:
                block_ack = block_ack >> 1
            else:
                return False
        return True

    def _add_segments(self, transport_pdu_info: TransportPDUInfo, segment: bytes) -> bool:
        self.segments_recv[transport_pdu_info.IN_seg_o] = segment
        return len(self.segments_recv) >= (transport_pdu_info.IN_seg_n + 1)

    def _assembly_segments(self) -> bytes:
        encrypted_access_pdu = b''
        for k in list(self.segments_recv.keys()):
            encrypted_access_pdu += self.segments_recv[k]
        return encrypted_access_pdu

    def _decrypt_pdu(self, transport_pdu_info: TransportPDUInfo, encrypted_pdu: bytes) -> (bytes, bool):
        encrypted_data = encrypted_pdu[0:-4] if transport_pdu_info.IN_szmic == 0 else encrypted_pdu[0:-8]
        transport_mic = encrypted_pdu[-4:] if transport_pdu_info.IN_szmic == 0 else encrypted_pdu[-8:]

        network = mesh_manager.networks[transport_pdu_info.network_name]
        app_key = mesh_manager.applications[transport_pdu_info.application_name].key
        app_nonce = b'\x01' + (transport_pdu_info.IN_szmic << 7).to_bytes(1, 'big') + transport_pdu_info.IN_seq + \
                    transport_pdu_info.src_addr.byte_value + transport_pdu_info.dst_addr.byte_value + network.iv_index

        aes_ccm_result = CRYPTO.aes_ccm(app_key, app_nonce, encrypted_data, b'')
        access_pdu = aes_ccm_result[0:-4] if transport_pdu_info.IN_szmic == 0 else aes_ccm_result[0:-8]
        calc_transport_mic = aes_ccm_result[-4:] if transport_pdu_info.IN_szmic == 0 else aes_ccm_result[-8:]
        if calc_transport_mic != transport_mic:
            return b'', False
        else:
            return access_pdu, True

    def _mount_block_ack(self):
        block_ack = 0x00
        for seg_o, segment in self.segments_recv:
            block_ack |= (0x01 << seg_o)
        return block_ack.to_bytes(4, 'big')

    def _send_ack(self, transport_pdu_info: TransportPDUInfo):
        block_ack = self._mount_block_ack()
        transport_pdu = b'\x00' + (transport_pdu_info.IN_seq_zero << 2).to_bytes(2, 'big') + block_ack
        network_pdu_info = NetworkPDUInfo(True, self.ttl, transport_pdu_info.IN_seq, transport_pdu_info.src_addr,
                                          transport_pdu_info.dst_addr, transport_pdu_info.network_name)
        self.network_layer.send_pdu(network_pdu_info, transport_pdu)

    def _resend_segments(self, transport_pdu_info: TransportPDUInfo):
        block_ack = transport_pdu_info.IN_block_ack

        missed_segments = []
        for x in range(transport_pdu_info.IN_seg_n + 1):
            ack_bit = block_ack & 0x01
            block_ack = block_ack >> 1
            if ack_bit == 0:
                missed_segments.append(self.last_segments_sent[x])

        network_pdu_info = NetworkPDUInfo(False, self.ttl, transport_pdu_info.IN_seq, transport_pdu_info.src_addr,
                                          transport_pdu_info.dst_addr, transport_pdu_info.network_name)
        for miss_seg in missed_segments:
            self.network_layer.send_pdu(network_pdu_info, miss_seg)

    def _start_ack_timer(self, transport_pdu_info: TransportPDUInfo):
        self.ack_info = transport_pdu_info
        self.ack_elapsed_time = 0
        self.ack_start_time = time()
        self.has_pending_ack = True

    def _ack_timer_t(self, self_task: Task):
        while True:
            if self.has_pending_ack:
                self.ack_start_time = time()
                yield
                if self.ack_elapsed_time >= self.ack_response_time and self.has_pending_ack:
                    self.ack_start_time = 0
                    self.ack_elapsed_time = 0
                    self.has_pending_ack = False
                    self._send_ack(self.ack_info)
                else:
                    self.ack_elapsed_time += time() - self.ack_start_time
            else:
                yield

    def _handle_recv_pdu(self, network_pdu_info, pdu, **kwarg):
        lookup_table_key = pdu[0:1]
        application_name = self.application_lookup_table[lookup_table_key]
        transport_pdu_info = TransportPDUInfo(network_pdu_info.src_addr, network_pdu_info.dst_addr,
                                              network_pdu_info.network_name, application_name)
        transport_pdu_info.IN_seq = network_pdu_info.seq

        if network_pdu_info.is_control_message:
            seg, opcode, obo = self._get_control_header(pdu)

            if seg == 0 and opcode == 0 and obo == 0:
                transport_pdu_info.IN_seq_zero = self._decode_seq_zero(pdu)
                transport_pdu_info.IN_block_ack = self._decode_block_ack(pdu)
                self.segment_is_acked = self._check_missed_acks(transport_pdu_info)
                if not self.segment_is_acked:
                    self._resend_segments(transport_pdu_info)
        else:
            if self._is_segmented(pdu):
                transport_pdu_info.IN_szmic = self._decode_szmic(pdu)
                transport_pdu_info.IN_seq_zero = self._decode_seq_zero(pdu)
                transport_pdu_info.IN_seg_o = self._decode_seg_o(pdu)
                transport_pdu_info.IN_seg_n = self._decode_seg_n(pdu)
                segment = self._decode_segment(pdu)

                is_last = self._add_segments(transport_pdu_info, segment)
                if not is_last:
                    self._start_ack_timer(transport_pdu_info)
                    return
                else:
                    self.has_pending_ack = False
                    self._send_ack(transport_pdu_info)
                encrypted_pdu = self._assembly_segments()
            else:
                encrypted_pdu = pdu[1:]

            access_pdu, is_valid = self._decrypt_pdu(transport_pdu_info, encrypted_pdu)
            if not is_valid:
                return
            self.new_message_signal.emit(transport_pdu_info=transport_pdu_info, pdu=access_pdu)

# Receive Section

# Send Section
    def _translate_pdu_info(self, transport_pdu_info: TransportPDUInfo) -> NetworkPDUInfo:
        return NetworkPDUInfo(False, self.ttl, self.seq.to_bytes(3, 'big'), transport_pdu_info.src_addr, transport_pdu_info.dst_addr,
                              transport_pdu_info.network_name)

    """
    All transport messages, in this first version, will be transport mic size equals to 32-bits
    """
    def _encrypt_pdu(self, access_pdu: bytes, transport_pdu_info: TransportPDUInfo) -> (bytes, bytes):
        network = mesh_manager.networks[transport_pdu_info.network_name]
        app_key = mesh_manager.applications[transport_pdu_info.application_name].key
        app_nonce = b'\x01' + (0x00 << 7).to_bytes(1, 'big') + self.seq.to_bytes(3, 'big') + transport_pdu_info.src_addr.byte_value + \
                    transport_pdu_info.dst_addr.byte_value + network.iv_index

        aes_ccm_result = CRYPTO.aes_ccm(app_key, app_nonce, access_pdu, b'')
        access_pdu_encrypted = aes_ccm_result[0:-4]
        transport_mic = aes_ccm_result[-4:]
        return access_pdu_encrypted, transport_mic

    @staticmethod
    def _need_segmentation(access_pdu: bytes) -> bool:
        return (len(access_pdu) + 4) > 15

    # TODO
    def _calc_seq_zero(self, iv_index: bytes, seq: int) -> int:
        pass

    def _mount_segmented_transport_pdu(self, transport_pdu_info: TransportPDUInfo, access_pdu: bytes,
                                       network: Network) -> (List[bytes]):
        transport_pdu_segments = []
        app_key = mesh_manager.applications[transport_pdu_info.application_name].key
        pdu = access_pdu

        afk = 0
        aid = int.from_bytes(CRYPTO.k4(app_key), 'big')
        first_byte = int((afk << 6) | (aid & 0x3f)).to_bytes(1, 'big')

        szmic = 0
        seq_zero = self._calc_seq_zero(network.iv_index, self.seq)
        seg_n = int((len(access_pdu) - 1) / 15)
        for seg_o in range(seg_n):
            header = first_byte + int(((szmic & 0x01) << 23) | ((seq_zero & 0x1fff) << 10) | (seg_o & 0x1f) |
                                      (seg_n & 0x1f)).to_bytes(3, 'big')
            segment_m = pdu[0:15]
            transport_pdu_segments.append(header + segment_m)
            pdu = pdu[15:]
        transport_pdu_segments.append(pdu)

        return transport_pdu_segments

    def _mount_unsegmented_transport_pdu(self, transport_pdu_info: TransportPDUInfo, access_pdu: bytes) -> bytes:
        app_key = mesh_manager.applications[transport_pdu_info.application_name].key

        afk = 0
        aid = int.from_bytes(CRYPTO.k4(app_key), 'big')

        first_byte = int((afk << 6) | (aid & 0x3f)).to_bytes(1, 'big')

        return first_byte + access_pdu

    def _start_giveup_timer(self, timeout: int):
        self.giveup_elapsed_time = 0
        self.giveup_timeout = timeout
        self.giveup_start_time = time()

    def _giveup_timer_blows_up(self) -> bool:
        return self.giveup_elapsed_time >= self.giveup_timeout

    def _update_giveup_timer(self):
        self.giveup_elapsed_time = time() - self.giveup_start_time

    """
    Send method resets the class variables
    """
    def send_pdu(self, transport_pdu_info: TransportPDUInfo, access_pdu: bytes, giveup_timeout=30):
        network_pdu_info = self._translate_pdu_info(transport_pdu_info)

        access_pdu_encrypted, transport_mic = self._encrypt_pdu(access_pdu, transport_pdu_info)
        final_pdu = access_pdu_encrypted + transport_mic

        if self._need_segmentation(access_pdu):
            transport_pdu_segments = self._mount_segmented_transport_pdu(transport_pdu_info, final_pdu)
            for x in range(len(transport_pdu_segments)):
                self.last_segments_sent[x] = transport_pdu_segments[x]
                self.network_layer.send_pdu(network_pdu_info, transport_pdu_segments[x])
        else:
            transport_pdu = self._mount_unsegmented_transport_pdu(transport_pdu_info, final_pdu)
            self.network_layer.send_pdu(network_pdu_info, transport_pdu)

        self._start_giveup_timer(giveup_timeout)

        while not self.segment_is_acked and not self._giveup_timer_blows_up():
            self._update_giveup_timer()

        self.seq += 1
# Send Section
