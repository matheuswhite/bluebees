#!/usr/bin/python3
from threading import Thread


# Thanks to @awesomebytes
# Source: https://gist.github.com/awesomebytes/0483e65e0884f05fb95e314c4f2b3db8
def threaded(fn):
    """To use as decorator to make a function call threaded.
    Needs import
    from threading import Thread"""
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


# Thanks to @berkerpeksag
# Source: https://github.com/berkerpeksag/python-playground/blob/master/borg.py
def borg(cls):
    """A class decorator for Borg design pattern."""
    cls._state = {}
    _new = cls.__new__

    def wrapper(self, *args, **kwargs):
        self.__dict__ = cls._state
        _new(self, *args, **kwargs)

    cls.__new__ = wrapper
    return cls


def check_none(value, case_none):
    return (value, case_none)[value is None]


def mask(value, mask_):
    return value & mask_
