from Crypto.Cipher import AES
from Crypto.Hash import CMAC
from ecdsa.ecdsa import Public_key, Private_key
from cryptography.hazmat.primitives.ciphers.aead import AESCCM
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import cmac
from cryptography.hazmat.primitives.ciphers import algorithms


class Crypto:

    def __init__(self):
        pass

    def e_encrypt(self, key: bytes, plaintext: bytes):
        cipher = AES.new(key, mode=AES.MODE_ECB)
        msg = cipher.encrypt(plaintext)
        return msg

    def e_decrypt(self, key: bytes, ciphertext: bytes):
        cipher = AES.new(key, mode=AES.MODE_ECB)
        msg = cipher.decrypt(ciphertext)
        return msg

    def aes_cmac(self, key: bytes, text: bytes):
        c = cmac.CMAC(algorithms.AES(key), backend=default_backend())
        c.update(text)
        return c.finalize()

    def aes_ccm_encrypt(self, key: bytes, nonce: bytes, text: bytes, adata: bytes):
        aesccm = AESCCM(key, tag_length=8)
        ct = aesccm.encrypt(nonce, text, adata)
        return ct

    def aes_ccm_decrypt(self, key: bytes, nonce: bytes, text: bytes, adata: bytes):
        aesccm = AESCCM(key, tag_length=8)
        ct = aesccm.decrypt(nonce, text, adata)
        return ct

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
        return (int.from_bytes((t1 + t2 + t3), 'big') % (2**263)).to_bytes(48, 'big')

    def k3(self, n: bytes):
        salt = self.s1(b'smk3')
        t = self.aes_cmac(salt, n)
        return (int.from_bytes(self.aes_cmac(t, b'id64' + b'\x01'), 'big') % (2**64)).to_bytes(16, 'big')

    def k4(self, n: bytes):
        salt = self.s1(b'smk4')
        t = self.aes_cmac(salt, n)
        return (int.from_bytes(self.aes_cmac(t, b'id6' + b'\x01'), 'big') % (2 ** 6)).to_bytes(16, 'big')


CRYPTO = Crypto()
