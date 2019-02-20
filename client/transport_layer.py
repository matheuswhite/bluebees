from client.address import MeshAddress
from client.network_layer import NetworkLayer, NetworkPDUInfo
from signalslot.signal import Signal
from typing import List


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


class UpperTransportLayer:

    def __init__(self, network_layer: NetworkLayer, default_ttl=3):
        self.network_layer = network_layer
        self.network_layer.new_message_signal.connect(self._handle_recv_pdu)

        self.new_message_signal = Signal(args=['transport_pdu_info', 'pdu'])
        self.seq = 0
        self.ttl = default_ttl

        # self.acks[seq_zero] = TransportAckHelper(seq_zero, seg_n)
        self.ack_helpers = {}

    # TODO
    def _authenticate_pdu(self, network_pdu_info: NetworkPDUInfo, network_pdu: bytes) -> bool:
        pass

    # TODO
    def _decrypt_pdu(self, network_pdu_info: NetworkPDUInfo, network_pdu: bytes) -> (TransportPDUInfo, bytes):
        transport_pdu_info: TransportPDUInfo
        access_pdu: bytes

        return transport_pdu_info, access_pdu

    # TODO
    def _update_acks(self, transport_pdu_info: TransportPDUInfo):
        pass

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

    def _handle_recv_pdu(self, network_pdu_info, pdu, **kwarg):
        is_valid = self._authenticate_pdu(network_pdu_info, pdu)
        if not is_valid:
            return

        transport_pdu_info, access_pdu = self._decrypt_pdu(network_pdu_info, pdu)

        self._update_acks(transport_pdu_info)

        self.new_message_signal.emit(transport_pdu_info=transport_pdu_info, pdu=access_pdu)

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
