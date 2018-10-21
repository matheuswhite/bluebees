#!/usr/bin/python3
from enum import Enum
from threading import Thread


# Thanks to @awesomebytes
# Source: https://gist.github.com/awesomebytes/0483e65e0884f05fb95e314c4f2b3db8
def threaded(fn):
    """To use as decorator to make a function call threaded.
    Needs import
    from threading import Thread"""
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper


class HandSide(Enum):
    Provisioner = 0
    Device = 1


def check_none(value, case_none):
    return (value, case_none)[value is None]


def mask(value, mask_):
    return value & mask_
