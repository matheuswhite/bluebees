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
        self.network_key_lookup_table = {}

    def _gen_security_material(self, network_id: bytes):
        materials = CRYPTO.k2(self.network_keys[network_id], b'\x00')
        nid = (materials & NID_MASK) >> 32
        encryption_key = (materials & ENCRYPTION_KEY_MASK) >> 16
        privacy_key = materials & PRIVACY_KEY_MASK
        return nid, encryption_key, privacy_key

    def _encrypt(self, is_control_message: bool, dst: bytes, transport_pdu: bytes, encryption_key: bytes,
                 network_nonce: bytes):
        aes_ccm_result = CRYPTO.aes_ccm_encrypt(encryption_key, network_nonce, dst + transport_pdu, b'')
        encrypted_data = aes_ccm_result[0:-8] if is_control_message else aes_ccm_result[0:-4]
        net_mic = aes_ccm_result[-8:] if is_control_message else aes_ccm_result[-4:]
        return encrypted_data[0:2], encrypted_data[2:], net_mic

    def _xor(self, a: bytes, b: bytes):
        r = b''
        for x in range(6):
            r += a[x] ^ b[x]
        return r

    def _obsfucate(self, ctl: int, ttl: int, seq: bytes, src: bytes, encrypted_dst: bytes,
                   encrypted_transport_pdu: bytes, net_mic: bytes, privacy_key: bytes):
        privacy_random = (encrypted_dst + encrypted_transport_pdu + net_mic)[0:7]
        pecb = CRYPTO.e_encrypt(privacy_key, b'\x00\x00\x00\x00\x00' + self.iv_index.to_bytes(4, 'big') + privacy_random)
        obsfucated_data = self._xor((ctl | ttl).to_bytes(1, 'big') + seq + src, pecb[0:6])
        return obsfucated_data

    def _clean_message(self, obfuscated: bytes, privacy_key: bytes, encrypted: bytes):
        privacy_random = encrypted[0:7]
        pecb = CRYPTO.e_decrypt(privacy_key, b'\x00\x00\x00\x00\x00' + self.iv_index.to_bytes(4, 'big') + privacy_random)
        clean_result = self._xor(obfuscated, pecb[0:6])
        return clean_result

    def _authenticate(self, is_control_message: bool, encrypted_data: bytes, net_mic: bytes, encryption_key: bytes,
                      network_nonce: bytes):
        aes_ccm_result = CRYPTO.aes_ccm_decrypt(encryption_key, network_nonce, encrypted_data, b'')
        decrypted_data = aes_ccm_result[0:-8] if is_control_message else aes_ccm_result[0:-4]
        calc_net_mic = aes_ccm_result[-8:] if is_control_message else aes_ccm_result[-4:]
        if calc_net_mic != net_mic:
            return False, None, None
        else:
            dst = decrypted_data[0:2]
            transport_pdu = decrypted_data[2:]
            return True, dst, transport_pdu

    def _handle_recv_message(self, msg):
        ivi = (msg[0] & 0x80) >> 7
        nid = msg[0] & 0x7f
        encryption_key = self.network_key_lookup_table[nid][0]
        privacy_key = self.network_key_lookup_table[nid][1]
        obfuscated = msg[1:7]

        clean = self._clean_message(obfuscated, privacy_key, msg[7:])
        ctl = (clean[0] & 0x80) >> 7
        ttl = clean[0] & 0x7f
        seq = clean[1:4]
        src = clean[4:6]

        net_mic = msg[-4:] if ctl == 0 else msg[-8:]
        encrypted_data = msg[9:-4] if ctl == 0 else msg[9:-8]
        network_nonce = b'\x00' + clean + b'\x00\x00' + self.iv_index.to_bytes(4, 'big')
        is_valid, dst, transport_pdu = self._authenticate(ctl == 1, encrypted_data, net_mic, encryption_key, network_nonce)

        if not is_valid:
            return

        self.new_message_signal.emit(msg=(src, dst, transport_pdu))

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

        self.network_key_lookup_table[nid] = (encryption_key, privacy_key)
        network_nonce = b'\x00' + (ctl | ttl).to_bytes(1, 'big') + seq.to_bytes(3, 'big') + src + b'\x00\x00' + \
                        self.iv_index.to_bytes(4, 'big')
        enc_dst, enc_transport_pdu, net_mic = self._encrypt(is_control_message, dst, transport_pdu, encryption_key,
                                                            network_nonce)
        obsfucated = self._obsfucate(ctl, ttl, seq.to_bytes(3, 'big'), src, enc_dst, enc_transport_pdu, net_mic,
                                     privacy_key)

        network_pdu = (ivi | nid).to_bytes(1, 'big') + obsfucated + enc_dst + enc_transport_pdu + net_mic

        self.driver.send(2, 20, network_pdu)

        self.seq += 1

    def recv_transport_pdu_t(self, self_task: Task):
        while self.is_alive:
            msg = self.driver.recv('message')
            if msg is not None:
                self._handle_recv_message(msg)
            yield
