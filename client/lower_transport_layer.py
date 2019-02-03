from client.address import MeshAddress
from client.network_layer import NetworkLayer
from signalslot.signal import Signal


class LowerTransportLayer:

    def __init__(self, network_layer: NetworkLayer):
        self.network_layer = network_layer
        self.network_layer.new_message_signal.connect(self._handle_pdu)

        self.new_message_signal = Signal(args=['src', 'dst', 'pdu'])
        self.message_sent_signal = Signal(args=['pdu'])

    def _handle_pdu(self, src, dst, pdu, **kwargs):
        if self._isack(pdu):
            self.message_sent_signal.emit(pdu=pdu)
        else:
            self.new_message_signal.emit(src=src, dst=dst, pdu=pdu)

    def send_pdu(self, src_addr: MeshAddress, dst_addr: MeshAddress, pdu: bytes, ttl: int, network_id: bytes):
        self.network_layer.send_pdu(src_addr, dst_addr, pdu, False, ttl, network_id)
