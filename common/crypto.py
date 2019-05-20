from Crypto.Cipher import AES
from Crypto.Hash import CMAC
from Crypto.Random import get_random_bytes


class Crypto:

    def __init__(self):
        pass

    def e(self, key: bytes, plaintext: bytes):
        cipher = AES.new(key, mode=AES.MODE_ECB)
        msg = cipher.encrypt(plaintext)
        return msg[0:6]

    def aes_cmac(self, key: bytes, text: bytes):
        cobj = CMAC.new(key=key, ciphermod=AES)
        cobj.update(text)
        return cobj.digest()

    def aes_ccm(self, key: bytes, nonce: bytes, text: bytes, adata: bytes):
        cypher = AES.new(key=key, mode=AES.MODE_CCM, nonce=nonce, mac_len=8, assoc_len=len(adata))
        cyphertext, tag = cypher.encrypt_and_digest(text + adata)
        return cyphertext[0:13]

    def aes_ccm_complete(self, key: bytes, nonce: bytes, text: bytes, adata: bytes, mic_size=8):
        cypher = AES.new(key=key, mode=AES.MODE_CCM, nonce=nonce, mac_len=mic_size, assoc_len=len(adata), msg_len=len(text))
        cyphertext, tag = cypher.encrypt_and_digest(text + adata)
        return cyphertext, tag

    def aes_ccm_decrypt(self, key: bytes, nonce: bytes, text: bytes, mic: bytes):
        cypher = AES.new(key=key, mode=AES.MODE_CCM, nonce=nonce, mac_len=len(mic))
        data = cypher.decrypt(text)
        try:
            cypher.verify(mic)
        except ValueError:
            check = False
        else:
            check = True
        return data, check

    def s1(self, text: bytes):
        return self.aes_cmac(key=b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', text=text)

    def k1(self, n: bytes, salt: bytes, p: bytes):
        t = self.aes_cmac(salt, n)
        return self.aes_cmac(key=t, text=p)

    def k2(self, n: bytes, p: bytes):
        salt = self.s1(b'smk2')
        t = self.aes_cmac(salt, n)
        t0 = b''
        t1 = self.aes_cmac(t, t0 + p + b'\x01')
        t2 = self.aes_cmac(t, t1 + p + b'\x02')
        t3 = self.aes_cmac(t, t2 + p + b'\x03')
        return (int.from_bytes((t1 + t2 + t3), 'big') % (2**263)).to_bytes(33, 'big')

    def k3(self, n: bytes):
        salt = self.s1(b'smk3')
        t = self.aes_cmac(salt, n)
        return (int.from_bytes(self.aes_cmac(t, b'id64' + b'\x01'), 'big') % (2**64)).to_bytes(8, 'big')

    def k4(self, n: bytes):
        salt = self.s1(b'smk4')
        t = self.aes_cmac(salt, n)
        return (int.from_bytes(self.aes_cmac(t, b'id6' + b'\x01'), 'big') % (2 ** 6)).to_bytes(1, 'big')


crypto = Crypto()
