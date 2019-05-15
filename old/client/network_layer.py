from client.address import MeshAddress
from core.dongle import DongleDriver
from core.scheduling import Task
from signalslot.signal import Signal
from client.crypto import CRYPTO
from model.mesh_manager import mesh_manager


NID_MASK = (0x7F << 32)
ENCRYPTION_KEY_MASK = (0xFFFF_FFFF_FFFF_FFFF << 16)
PRIVACY_KEY_MASK = 0xFFFF_FFFF_FFFF_FFFF


class NetworkPDUInfo:

    def __init__(self, is_control_message: bool, ttl: int, seq: bytes, src_addr: MeshAddress, dst_addr: MeshAddress,
                 network_id: bytes):
        self.is_control_message = is_control_message
        self.ttl = ttl
        self.seq = seq
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.network_id = network_id


# header = (13 or 17) && pdu = 16
# max size 33
# min size 18
class NetworkLayer:

    def __init__(self, driver: DongleDriver):
        self.driver = driver
        self.new_message_signal = Signal(args=['network_pdu_info', 'pdu'])

        self.is_alive = True
        self.iv_index = 0x0000_0000
        self.network_keys = {}
        self.network_key_lookup_table = {}
        self._update_network_keys()

    def _update_network_keys(self):
        networks = list(mesh_manager.networks.values())
        for net in networks:
            network_id = self.network_id(net.key)
            self.network_keys[network_id] = net.key

            materials = CRYPTO.k2(net.key, b'\x00')
            nid = (materials & NID_MASK) >> 32
            encryption_key = (materials & ENCRYPTION_KEY_MASK) >> 16
            privacy_key = materials & PRIVACY_KEY_MASK
            self.network_key_lookup_table[nid] = (encryption_key, privacy_key, network_id)

    def _gen_security_material(self, network_id: bytes):
        materials = CRYPTO.k2(self.network_keys[network_id], b'\x00')
        nid = (materials & NID_MASK) >> 32
        encryption_key = (materials & ENCRYPTION_KEY_MASK) >> 16
        privacy_key = materials & PRIVACY_KEY_MASK
        return nid, encryption_key, privacy_key

    def _encrypt(self, is_control_message: bool, dst: bytes, transport_pdu: bytes, encryption_key: bytes,
                 network_nonce: bytes):
        aes_ccm_result = CRYPTO.aes_ccm(encryption_key, network_nonce, dst + transport_pdu, b'')
        encrypted_data = aes_ccm_result[0:-8] if is_control_message else aes_ccm_result[0:-4]
        net_mic = aes_ccm_result[-8:] if is_control_message else aes_ccm_result[-4:]
        return encrypted_data[0:2], encrypted_data[2:], net_mic

    def _xor(self, a: bytes, b: bytes):
        r = b''
        for x in range(6):
            r += a[x] ^ b[x]
        return r

    def _obfuscate(self, ctl: int, ttl: int, seq: bytes, src: bytes, encrypted_dst: bytes,
                   encrypted_transport_pdu: bytes, net_mic: bytes, privacy_key: bytes):
        privacy_random = (encrypted_dst + encrypted_transport_pdu + net_mic)[0:7]
        pecb = CRYPTO.e(privacy_key, b'\x00\x00\x00\x00\x00' + self.iv_index.to_bytes(4, 'big') + privacy_random)
        obsfucated_data = self._xor((ctl | ttl).to_bytes(1, 'big') + seq + src, pecb[0:6])
        return obsfucated_data

    def _clean_message(self, obfuscated: bytes, privacy_key: bytes, encrypted: bytes):
        privacy_random = encrypted[0:7]
        pecb = CRYPTO.e(privacy_key, b'\x00\x00\x00\x00\x00' + self.iv_index.to_bytes(4, 'big') + privacy_random)
        clean_result = self._xor(obfuscated, pecb[0:6])
        return clean_result

    def _authenticate(self, is_control_message: bool, encrypted_data: bytes, net_mic: bytes, encryption_key: bytes,
                      network_nonce: bytes):
        aes_ccm_result = CRYPTO.aes_ccm(encryption_key, network_nonce, encrypted_data, b'')
        decrypted_data = aes_ccm_result[0:-8] if is_control_message else aes_ccm_result[0:-4]
        calc_net_mic = aes_ccm_result[-8:] if is_control_message else aes_ccm_result[-4:]
        if calc_net_mic != net_mic:
            return False, None, None
        else:
            dst = decrypted_data[0:2]
            transport_pdu = decrypted_data[2:]
            return True, dst, transport_pdu

    def _handle_recv_pdu(self, msg):
        ivi = (msg[0] & 0x80) >> 7
        nid = msg[0] & 0x7f
        encryption_key = self.network_key_lookup_table[nid][0]
        privacy_key = self.network_key_lookup_table[nid][1]
        network_id = self.network_key_lookup_table[nid][2]
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

        network_pdu_info = NetworkPDUInfo(ctl == 1, ttl, seq, src, dst, network_id)

        self.new_message_signal.emit(network_pdu_info=network_pdu_info, pdu=transport_pdu)

    def kill(self):
        self.is_alive = False

    @classmethod
    def network_id(cls, network_key: bytes):
        return CRYPTO.k3(network_key)

    def send_pdu(self, network_pdu_info: NetworkPDUInfo, transport_pdu: bytes):
        if not (1 <= len(transport_pdu) <= 16):
            return

        self._update_network_keys()

        ivi = (self.iv_index & 0x01) << 7
        nid, encryption_key, privacy_key = self._gen_security_material(network_pdu_info.network_id)
        ctl = 0x80 if network_pdu_info.is_control_message else 0x00
        ttl = network_pdu_info.ttl & 0x7f
        seq = network_pdu_info.seq
        src = network_pdu_info.src_addr.byte_value
        dst = network_pdu_info.dst_addr.byte_value

        network_nonce = b'\x00' + (ctl | ttl).to_bytes(1, 'big') + seq + src + b'\x00\x00' + \
                        self.iv_index.to_bytes(4, 'big')
        enc_dst, enc_transport_pdu, net_mic = self._encrypt(network_pdu_info.is_control_message, dst, transport_pdu,
                                                            encryption_key, network_nonce)
        obsfucated = self._obfuscate(ctl, ttl, seq, src, enc_dst, enc_transport_pdu, net_mic,
                                     privacy_key)

        network_pdu = (ivi | nid).to_bytes(1, 'big') + obsfucated + enc_dst + enc_transport_pdu + net_mic

        self.driver.send(2, 20, network_pdu)

    def recv_pdu_t(self, self_task: Task):
        while self.is_alive:
            pdu = self.driver.recv('message')
            if pdu is not None:
                self._update_network_keys()
                self._handle_recv_pdu(pdu)
            yield
