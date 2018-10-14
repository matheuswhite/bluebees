

class Buffer:

    def __init__(self):
        self.__buff = b''

    @property
    def buffer(self):
        return self.__buff

    # PUSH

    def push_u8(self, byte):
        pass

    def push_be16(self, value):
        pass

    def push_le16(self, value):
        pass

    def push_be32(self, value):
        pass

    def push_le32(self, value):
        pass

    def push_be(self, value: bytes):
        pass

    def push_le(self, value: bytes):
        pass

    # PULL

    def pull_u8(self):
        pass

    def pull_be16(self):
        pass

    def pull_le16(self):
        pass

    def pull_be32(self):
        pass

    def pull_le32(self):
        pass

    def pull_be(self, size):
        pass

    def pull_le(self, size):
        pass

    # SEEK

    def seek(self, index):
        pass
