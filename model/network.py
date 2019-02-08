from client.network_layer import NetworkLayer


class Network:

    def __init__(self, key: bytes):
        self.key = key
        self.index = NetworkLayer.network_id(self.key)
