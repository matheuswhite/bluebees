from core.buffer import Buffer


class Message:

    def __init__(self):
        self.header = Buffer()
        self.payload = Buffer()

    def to_bytes(self):
        return self.header.buffer + self.payload.buffer

    def encode_msg(self, **kwargs):
        pass

    @staticmethod
    def decode_msg(buffer: Buffer):
        pass
