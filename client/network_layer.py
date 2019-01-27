from client.address import MeshAddress
from core.dongle import DongleDriver
from core.scheduling import Task
from signalslot.signal import Signal
from client.crypto import CRYPTO

NID_MASK = (0x7F << 32)
ENCRYPTION_KEY_MASK = (0xFFFF_FFFF_FFFF_FFFF << 16)
PRIVACY_KEY_MASK = 0xFFFF_FFFF_FFFF_FFFF


# header = (13 or 17) && pdu = 16
# max size 33
# min size 18
class NetworkLayer:

    def __init__(self, driver: DongleDriver):
        self.driver = driver
        self.new_message_signal = Signal(args=['msg'])

        self.is_alive = True
        self.iv_index = 0x0000_0000
        self.seq = 0x00_0000
        self.network_keys = {}

    def _gen_security_material(self, network_id: bytes):
        materials = CRYPTO.k2(self.network_keys[network_id], b'\x00')
        nid = (materials & NID_MASK) >> 32
        encryption_key = (materials & ENCRYPTION_KEY_MASK) >> 16
        privacy_key = materials & PRIVACY_KEY_MASK
        return nid, encryption_key, privacy_key

    def _gen_netmic(self, is_control_message: bool, dst: bytes, transport_pdu: bytes):
        # net_mic = b'\x00\x00\x00\x00' or b'\x00\x00\x00\x00\x00\x00\x00\x00'
        raise NotImplementedError

    def _encrypt(self, dst: bytes, transport_pdu: bytes):
        raise NotImplementedError

    def _encrypt2(self, enc_dst: bytes, enc_transport_pdu: bytes):
        raise NotImplementedError

    def _obsfucate(self, ctl, ttl, seq, src):
        raise NotImplementedError

    def _authenticate(self):
        raise NotImplementedError

    def _handle_recv_message(self, msg):
        ivi = (msg[0] & 0x80) >> 7
        nid = msg[0] & 0x7f
        encryption_key = 0 # ???
        privacy_key = 0 # ???
        ctl = (msg[1] & 0x80) >> 7
        ttl = msg[1] & 0x7f
        seq = msg[2:5]
        src = msg[5:7]
        dst = msg[7:9]
        transport_pdu = msg[9:-4] if ctl == 0 else msg[9:-8]
        net_mic = msg[-4:] if ctl == 0 else msg[-8:]

        if not self._authenticate():
            return

        msg = transport_pdu

        self.new_message_signal.emit(msg=msg)

    def kill(self):
        self.is_alive = False

    @classmethod
    def network_id(cls, network_key: bytes):
        return CRYPTO.k3(network_key)

    def add_network_key(self, network_key: bytes):
        network_id = self.network_id(network_key)
        self.network_keys[network_id] = network_key

    def send_transport_pdu(self, src_addr: MeshAddress, dst_addr: MeshAddress, transport_pdu: bytes,
                           is_control_message: bool, ttl: int, network_id: bytes):
        if not (1 <= len(transport_pdu) <= 16):
            return

        ivi = (self.iv_index & 0x01) << 7
        nid, encryption_key, privacy_key = self._gen_security_material(network_id)
        ctl = 0x80 if is_control_message else 0x00
        ttl = ttl & 0x7f
        seq = self.seq
        src = src_addr.byte_value
        dst = dst_addr.byte_value
        net_mic = self._gen_netmic(is_control_message, dst, transport_pdu)

        enc_dst, enc_transport_pdu = self._encrypt(dst, transport_pdu)
        encrypted = self._encrypt2(enc_dst, enc_transport_pdu)
        obsfucated = self._obsfucate(ctl, ttl, seq, src)

        network_pdu = (ivi | nid).to_bytes(1, 'big') + obsfucated + encrypted + net_mic

        self.driver.send(2, 20, network_pdu)

    def recv_transport_pdu_t(self, self_task: Task):
        while self.is_alive:
            msg = self.driver.recv('message')
            yield
            if msg is not None:
                self._handle_recv_message(msg)
            yield
