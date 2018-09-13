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


# Thanks to @yuvalpinter
# Source: https://github.com/faif/python-patterns/blob/master/creational/borg.py
class Borg(object):
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state


def check_none(value, case_none):
    return (value, case_none)[value is None]


def mask(value, mask_):
    return value & mask_
