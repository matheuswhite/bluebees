from client.address import MeshAddress
from client.network_layer import NetworkLayer, NetworkPDUInfo
from signalslot.signal import Signal
from typing import List
from client.crypto import CRYPTO


class TransportAckHelper:

    def __init__(self, seq_zero, seg_n):
        self.seq_zero = seq_zero
        self.seg_n = seg_n
        self.acks = {}

    def ack(self, seg_o: int):
        if seg_o <= self.seg_n:
            self.acks[seg_o] = True

    def check(self, seg_o) -> bool:
        if seg_o <= self.seg_n:
            return self.acks[seg_o]
        return False

    def all_check(self) -> bool:
        for x in range(self.seg_n):
            if x not in list(self.acks.keys()):
                return False
            if not self.acks[x]:
                return False
        return True


class TransportPDUInfo:

    def __init__(self, src_addr: MeshAddress, dst_addr: MeshAddress, network_name: str, application_name: str):
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.network_name = network_name
        self.application_name = application_name
        self.IN_seq_zero = None
        self.IN_block_ack = None
        self.IN_seg_o = None
        self.IN_seg_n = None
        self.IN_szmic = None


class UpperTransportLayer:

    def __init__(self, network_layer: NetworkLayer, default_ttl=3):
        self.network_layer = network_layer
        self.network_layer.new_message_signal.connect(self._handle_recv_pdu)

        self.new_message_signal = Signal(args=['transport_pdu_info', 'pdu'])
        self.seq = 0
        self.ttl = default_ttl

        # self.acks[seq_zero] = TransportAckHelper(seq_zero, seg_n)
        self.ack_helpers = {}
        self.application_lookup_table = {}

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

    # TODO
    def _update_segments(self, transport_pdu_info: TransportPDUInfo, segment: bytes) -> bool:
        is_last: bool
        return is_last

    # TODO
    def _assembly_segments(self, transport_pdu_info: TransportPDUInfo) -> bytes:
        encrypted_access_pdu: bytes
        return encrypted_access_pdu

    # TODO
    def _decrypt_pdu(self, transport_pdu_info: TransportPDUInfo, encrypted_access_pdu: bytes) -> (bytes, bool):
        # app_key = self.application_lookup_table[transport_pdu_info.application_name]
        # app_nonce = b''
        # aes_ccm_result = CRYPTO.aes_ccm(app_key, app_nonce, transport_pdu)
        return b'', False

    # TODO
    def _update_acks(self, transport_pdu_info: TransportPDUInfo):
        # use ack helpers
        # see '_is_acked' method
        pass

    def _handle_recv_pdu(self, network_pdu_info, pdu, **kwarg):
        transport_pdu_info = TransportPDUInfo(network_pdu_info.src_addr, network_pdu_info.dst_addr,
                                              network_pdu_info.network_name, '')

        if network_pdu_info.is_control_message:
            seg, opcode, obo = self._get_control_header(pdu)

            if seg == 0 and opcode == 0 and obo == 0:
                transport_pdu_info.IN_seq_zero = self._decode_seq_zero(pdu)
                transport_pdu_info.IN_block_ack = self._decode_block_ack(pdu)
                self._update_acks(transport_pdu_info)
        else:
            if self._is_segmented(pdu):
                transport_pdu_info.IN_szmic = self._decode_szmic(pdu)
                transport_pdu_info.IN_seq_zero = self._decode_seq_zero(pdu)
                transport_pdu_info.IN_seg_o = self._decode_seg_o(pdu)
                transport_pdu_info.IN_seg_n = self._decode_seg_n(pdu)
                segment = self._decode_segment(pdu)
                is_last = self._update_segments(transport_pdu_info, segment)
                if not is_last:
                    return
                encrypted_access_pdu = self._assembly_segments(transport_pdu_info)
            else:
                lookup_table_key = pdu[0]
                transport_pdu_info.application_name = self.application_lookup_table[lookup_table_key]
                encrypted_access_pdu = pdu[1:]

            access_pdu, is_valid = self._decrypt_pdu(transport_pdu_info, encrypted_access_pdu)
            if not is_valid:
                return
            self.new_message_signal.emit(transport_pdu_info=transport_pdu_info, pdu=access_pdu)

# Receive Section

# Send Section
    # TODO
    def _translate_pdu_info(self, transport_pdu_info: TransportPDUInfo) -> NetworkPDUInfo:
        pass

    # TODO
    def _encrypt_pdu(self, access_pdu: bytes) -> bytes:
        pass

    # TODO
    def _need_segmentation(self, access_pdu: bytes) -> bool:
        pass

    # TODO
    def _mount_segmented_transport_pdu(self, transport_pdu_info: TransportPDUInfo, access_pdu: bytes) -> (List[bytes],
                                                                                                          List[bytes]):
        transport_pdu_info_segments = []
        transport_pdu_segments = []

        # code

        self.seq += 1
        return transport_pdu_info_segments, transport_pdu_segments

    # TODO
    def _mount_unsegmented_transport_pdu(self, transport_pdu_info: TransportPDUInfo, access_pdu: bytes) -> bytes:
        pass

    # TODO
    def _start_timer(self, timeout: int):
        pass

    # TODO
    def _timer_blows_up(self) -> bool:
        pass

    def _remove_ack_helper(self, transport_pdu_info: TransportPDUInfo):
        if transport_pdu_info.IN_seq_zero in list(self.ack_helpers.keys()):
            del self.ack_helpers[transport_pdu_info.IN_seq_zero]

    def _is_acked(self, transport_pdu_info: TransportPDUInfo) -> bool:
        if transport_pdu_info.IN_seq_zero not in list(self.ack_helpers.keys()):
            return False
        return self.ack_helpers[transport_pdu_info.IN_seq_zero].all_check()

    def send_pdu(self, transport_pdu_info: TransportPDUInfo, access_pdu: bytes, ack_timeout=30):
        network_pdu_info = self._translate_pdu_info(transport_pdu_info)

        access_pdu_encrypted = self._encrypt_pdu(access_pdu)

        if self._need_segmentation(access_pdu):
            transport_pdu_info_segments, transport_pdu_segments = self._mount_segmented_transport_pdu(
                transport_pdu_info,
                access_pdu_encrypted
            )
            for x in range(len(transport_pdu_segments)):
                self.network_layer.send_pdu(
                    transport_pdu_info_segments[x],
                    transport_pdu_segments[x]
                )
        else:
            transport_pdu = self._mount_unsegmented_transport_pdu(transport_pdu_info, access_pdu_encrypted)
            self.network_layer.send_pdu(network_pdu_info, transport_pdu)

        self._start_timer(ack_timeout)

        while not self._is_acked(transport_pdu_info) and not self._timer_blows_up():
            pass

        self._remove_ack_helper(transport_pdu_info)

# Send Section
