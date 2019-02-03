from client.address import MeshAddress
from client.upper_transport_layer import UpperTransportLayer
from core.scheduling import *
from threading import Event
from signalslot.signal import Signal


class AccessLayer:

    def __init__(self, upper_transport_layer: UpperTransportLayer):
        self.upper_transport_layer = upper_transport_layer
        self.upper_transport_layer.new_message_signal()
        self.upper_transport_layer.message_sent_signal.connect(self._message_sent_callback)

        self.max_ttl = 10
        self.message_sent_evts = {}
        self.new_message_signals = {}

    def _message_sent_callback(self, pdu, **kwargs):
        evt: Event = self.message_sent_evts[pdu]
        evt.set()

    def _handle_incoming_message(self, src, dst, pdu, **kwargs):
        opcode = self._get_opcode(pdu)
        if opcode in self.new_message_signals.keys():
            sig: Signal = self.new_message_signals[opcode]
            parameters = self._get_parameters(pdu)
            sig.emit(src=src, dst=dst, opcode=opcode, parameters=parameters)

    def get_new_message_signal(self, opcode: bytes):
        if opcode in self.new_message_signals.keys():
            return self.new_message_signals[opcode]
        else:
            sig = Signal(args=['src', 'dst', 'opcode', 'parameters'])
            self.new_message_signals[opcode] = sig
            return sig

    def send_message_t(self, self_task: Task, src_add: MeshAddress, dst_addr: MeshAddress, network_id: bytes,
                       opcode: bytes, parameters: bytes):
        ttl = 0
        pdu = opcode + parameters
        evt = Event()
        was_sent = False

        while not was_sent and self.max_ttl < ttl:
            self.message_sent_evts[pdu] = evt
            self.upper_transport_layer.send_pdu(src_add, dst_addr, pdu, ttl, network_id)
            self_task.wait_event(evt, 10)
            yield

            if self_task.timer.is_over:
                ttl += 1
            else:
                was_sent = True
