

class Buffer:

    def __init__(self):
        self.__buff = b''

    @property
    def buffer(self):
        return self.__buff

    @property
    def length(self):
        return len(self.buffer)

    def __len__(self):
        return len(self.buffer)

    def buffer_le(self):
        return self.__buff[::-1]

    def buffer_be(self):
        return self.__buff

    def clear(self):
        self.__buff = b''

    # PUSH

    def push_u8(self, byte):
        if type(byte) == bytes:
            byte = byte[0]
        self.__buff += int(byte).to_bytes(1, 'big')

    def push_be16(self, value):
        if type(value) == bytes:
            self.__buff += value[0:2]
        elif type(value) == int:
            self.__buff += int(value).to_bytes(2, 'big')

    def push_le16(self, value):
        if type(value) == bytes:
            self.__buff += value[0:2][::-1]
        elif type(value) == int:
            self.__buff += int(value).to_bytes(2, 'little')

    def push_be32(self, value):
        if type(value) == bytes:
            self.__buff += value[0:4]
        elif type(value) == int:
            self.__buff += int(value).to_bytes(4, 'big')

    def push_le32(self, value):
        if type(value) == bytes:
            self.__buff += value[0:4][::-1]
        elif type(value) == int:
            self.__buff += int(value).to_bytes(4, 'little')

    def push_be(self, value: bytes):
        self.__buff += value

    def push_le(self, value: bytes):
        self.__buff += value[::-1]

    # PULL

    def pull_u8(self):
        byte = self.__buff[0:1]
        self.__buff = self.__buff[1:]
        return byte

    def pull_be16(self):
        value = self.__buff[0:2]
        self.__buff = self.__buff[2:]
        return value

    def pull_le16(self):
        value = self.__buff[0:2]
        value = value[::-1]
        self.__buff = self.__buff[2:]
        return value

    def pull_be32(self):
        value = self.__buff[0:4]
        self.__buff = self.__buff[4:]
        return value

    def pull_le32(self):
        value = self.__buff[0:4]
        value = value[::-1]
        self.__buff = self.__buff[4:]
        return value

    def pull_be(self, size):
        value = self.__buff[0:size]
        self.__buff = self.__buff[size:]
        return value

    def pull_le(self, size):
        value = self.__buff[0:size]
        value = value[::-1]
        self.__buff = self.__buff[size:]
        return value

    def pull_all_be(self):
        value = self.__buff
        self.__buff = b''
        return value

    def pull_all_le(self):
        value = self.__buff
        value = value[::-1]
        self.__buff = b''
        return value

    # SEEK

    def seek(self, index):
        return self.__buff[index:index+1]
