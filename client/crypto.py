

class Crypto:

    def __init__(self):
        pass

    def e(self, key, plaintext):
        raise NotImplementedError

    def aes_cmac(self, key, text):
        raise NotImplementedError

    def aes_ccm(self, key, nonce, text, adata):
        raise NotImplementedError

    def s1(self, text):
        raise NotImplementedError

    def k1(self, key, salt, info):
        raise NotImplementedError

    def k2(self, key, info):
        raise NotImplementedError

    def k3(self, key):
        raise NotImplementedError

    def k4(self, key):
        raise NotImplementedError


CRYPTO = Crypto()
