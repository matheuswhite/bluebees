#!/usr/bin/python3
import sys

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine, QQmlComponent
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout
from time import sleep as time_sleep
from random import randrange
from threading import Thread


# Threaded function snippet
def threaded(fn):
    """To use as decorator to make a function call threaded.
    Needs import
    from threading import Thread"""
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


class AData:

    def __init__(self, data):
        self.__data = data
        self.__marks = []

    def consume(self, mark):
        if mark not in self.__marks:
            self.__marks.append(mark)
            return self.__data
        return None


class AQueue:

    def __init__(self):
        self.__queue = []

    def put(self, data: AData):
        self.__queue.append(data)

    def get(self, mark):
        for data in self.__queue:
            out = data.consume(mark)
            if out is not None:
                return out
        return None

    def __len__(self):
        return len(self.__queue)

    def clear(self, size):
        self.__queue = self.__queue[size:]

    def clear_all(self):
        self.__queue = []


class AProducer:

    def __init__(self):
        self.__buffer = 'Hel0 Wor1d'
        self.__queue = AQueue()

    def produce(self):
        time_sleep(randrange(0, 5))
        data = self.__buffer[randrange(0, len(self.__buffer))]
        if len(self.__queue) >= 100:
            self.__queue.clear(20)
        self.__queue.put(AData(data))

    def read(self, mark):

        data = self.__queue.get(mark)

        if data is None:
            print('[{}] Waiting produce...'.format(mark))
            self.produce()

        return self.__queue.get(mark)


class ALayer1(QObject):

    # signal
    dataRead = pyqtSignal(str, arguments=['data'])
    readingCompleted = pyqtSignal(int, arguments=['none'])
    readingStarted = pyqtSignal()

    def __init__(self, prod, name):
        QObject.__init__(self)

        self.__prod = prod
        self.__mark = name

    @property
    def mark(self):
        return self.__mark

    @threaded
    def read(self):
        self.readingStarted.emit()
        for _ in range(0, 5):
            data = self.__prod.read(self.__mark)
            print('[{}] - Data: {}'.format(self.__mark, data))
            self.dataRead.emit(data)
        self.readingCompleted.emit(1)

    @pyqtSlot()
    def start_read(self):
        self.read()


if __name__ == '__main__':
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    producer = AProducer()
    consumer1 = ALayer1(producer, 'C1')

    engine.rootContext().setContextProperty('consumer1', consumer1)
    engine.load('simple.qml')

    engine.quit.connect(app.quit)
    sys.exit(app.exec_())
