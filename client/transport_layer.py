from client.address import MeshAddress
from client.network_layer import NetworkLayer
from signalslot.signal import Signal


class UpperTransportLayer:

    def __init__(self, network_layer: NetworkLayer):
        self.network_layer = network_layer
        self.lower_transport_layer.new_message_signal.connect(self._handle_pdu)
        self.lower_transport_layer.message_sent_signal.connect(self._handle_message_sent)

        self.new_message_signal = Signal(args=['src', 'dst', 'pdu'])
        self.message_sent_signal = Signal(args=['pdu'])

    def _handle_message_sent(self, pdu, **kwargs):
        self.message_sent_signal.emit(pdu=pdu)

    def _handle_pdu(self, src, dst, pdu, **kwarg):
        self.new_message_signal.emit(src=src, dst=dst, pdu=pdu)

    def send_pdu(self, src_addr: MeshAddress, dst_addr: MeshAddress, pdu: bytes, ttl: int, network_id: bytes):
        self.lower_transport_layer.send_pdu(src_addr, dst_addr, pdu, ttl, network_id)
