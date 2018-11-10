#!/usr/bin/python3
from threading import Thread, Event
from time import time


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


def timer(timeout, event: Event):
    start_time = time()
    elapsed_time = time() - start_time
    while elapsed_time < timeout:
        elapsed_time = time() - start_time
    event.set()


def check_none(value, case_none):
    return (value, case_none)[value is None]


def mask(value, mask_):
    return value & mask_
