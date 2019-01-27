from client.message_gate import message_gate
from client.network_layer import NetworkLayer, MeshAddress, MeshAddressType
from core.scheduling import scheduler, Task
from client.model import Message

class Element:

    def __init__(self, address: MeshAddress):
        self.address = address
        self.upper_transport_layer = UpperTransportLayer()
        self.lower_transport_layer = LowerTransportLayer()
        self.network_layer = NetworkLayer()

    def send_message(self, dst_addr: MeshAddress, message: Message):
        access_pdu = message.opcode + message.parameters
        upper_tr_pdu = self.upper_transport_layer()
        lower_tr_pdu = self.lower_transport_layer.encode_lower_transport_pdu(''' args ''')
        network_pdu = self.network_layer.encode_network_pdu(self.address, dst_addr, lower_tr_pdu, False, self.defalt_ttl)

    """
    Returns
        -> src_addr [MeshAddress]
        -> message [Message]
    Errors
        Nothing
    """
    def recv_message_t(self, self_task: Task):
        pass
