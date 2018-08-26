#!/usr/bin/python3
from time import time


class Transaction:

    def __init__(self, transaction_number: int):
        # link ack
        self.__elapsed_time = time()
        self.__transaction_number = transaction_number
        self.was_ack = False

        # tr ack
        self.__timer = time()

    @property
    def transaction_number(self):
        return self.__transaction_number

    @property
    def elapsed_time(self):
        return self.__elapsed_time

    def increase_elapsed_time(self):
        self.__elapsed_time += self.elapsed_time - time()

    def stop_timer(self):
        self.__timer = -1

    def get_timer_value(self):
        self.__timer += self.__timer - time()
        return self.__timer
