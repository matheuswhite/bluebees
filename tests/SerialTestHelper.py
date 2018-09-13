from core.utils import threaded
from threading import RLock
from serial import Serial


class SerialTestHelper:

    def __init__(self, port: str):
        self.serial = Serial(port, 115200)
        self.message_queue = []
        self.lock = RLock()

        self.__listen()

    @threaded
    def __listen(self):
        while True:
            self.__atomic_read()

    def __atomic_read(self):
        while True:
            with self.serial:
                msg = self.serial.readline()
            if msg[0] == '@':
                with self.lock:
                    self.message_queue.append(msg)
                break

    def pop_message(self, topic: str):
        msg = None
        is_empty = True

        while is_empty:
            with self.lock:
                if len(self.message_queue) == 0:
                    is_empty = False

        with self.lock:
            for x in range(len(self.message_queue)):
                msg = self.message_queue[x]
                msg = msg.replace(" ", "")
                if msg[0:len(topic)] == topic:
                    msg = msg[len(topic):]
                    del self.message_queue[x]
                    break
        return msg

    # usage
    #
    # ser = SerialTestHelper('/dev/ttyACM1')
    # msg = ser.pop_message(topic='@prov')

