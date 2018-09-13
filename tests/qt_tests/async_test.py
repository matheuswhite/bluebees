#!/usr/bin/python3
from time import sleep as time_sleep
from random import randrange
from asyncio import Task, sleep
import asyncio


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

    async def produce(self):
        time_sleep(randrange(0, 5))
        data = self.__buffer[randrange(0, len(self.__buffer))]
        if len(self.__queue) >= 100:
            self.__queue.clear(20)
        self.__queue.put(AData(data))

    async def read(self, mark):
        print('[{}] Waiting produce...'.format(mark))
        await self.produce()
        data = self.__queue.get(mark)

        await sleep(0)
        if data is not None:
            return data


class ALayer1:

    def __init__(self, prod, name):
        self.__prod = prod
        self.__mark = name

    @property
    def mark(self):
        return self.__mark

    async def read(self):
        for _ in range(0, 5):
            data = await self.__prod.read(self.__mark)
            print('[{}] - Data: {}'.format(self.__mark, data))


# ----- TEST -----
producer = AProducer()
consumer1 = ALayer1(producer, '1')
consumer2 = ALayer1(producer, '2')

tasks = [Task(consumer1.read()), Task(consumer2.read())]

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
