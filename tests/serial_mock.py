from time import sleep


class SerialMock:

    def __init__(self, read_content: list):
        self.read_content = read_content
        self.read_index = -1
        self.write_content = []
        self.temp_write = []
        self.erros = []
        self.is_open = False

    def open(self):
        if not self.is_open:
            self.is_open = True
        else:
            self.erros.append('Already Open')

    def close(self):
        if self.is_open:
            self.is_open = False
        else:
            self.erros.append('Not Open')

    def readline(self):
        if not self.is_open:
            self.erros.append('Not Open')
            return None

        self.read_index += 1
        if self.read_index >= len(self.read_content):
            self.read_index = 0
        sleep(0.1)
        return self.read_content[self.read_index]

    def write(self, data: bytes):
        if not self.is_open:
            self.erros.append('Not Open')
            return None

        self.temp_write.append(data)
        if data[-1:] == b'\n':
            content = b''
            for d in self.temp_write:
                content += d
            self.write_content.append(content)
            self.temp_write = []