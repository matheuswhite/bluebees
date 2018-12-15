from collections import deque
from time import time
from dataclasses import dataclass
from core.log import Log, LogLevel
from typing import Any
from core.utils import threaded
from threading import Event


log = Log('Scheduler')
log.level = LogLevel.Inf.value


def timer_task(timeout_, event: Event):
    elapsed_time = 0
    while elapsed_time < timeout_:
        ts = time()
        yield
        elapsed_time += time() - ts
    event.set()


@dataclass
class Task:
    name: str
    start_time: float
    elapsed_time: float
    run: Any


class Scheduler:

    def __init__(self):
        self.tasks = deque()
        self.task_persistent = deque()

    def new_task(self, name: str, run):
        t = Task(name, 0, 0, run)
        self.tasks.append(t)
        self.task_persistent.append(t)

    def get_task_metadata(self, name):
        for t in self.task_persistent:
            if t.name == name:
                return t

    def run(self):
        while self.tasks:
            t = self.tasks.popleft()
            try:
                ts = time()
                log.dbg(f'Start task {t.name}')
                next(t.run)
                log.dbg(f'Yield task {t.name}')
                te = time()
                t.elapsed_time += te - ts
                t.start_time = ts
                self.tasks.append(t)
            except StopIteration:
                pass


scheduler = Scheduler()

if __name__ == '__main__':
    def countdown(n):
        while n > 0:
            print(f'T-minus{n}')
            yield
            n -= 1
        print('Blastoff!')

    def countup(n):
        x = 0
        while x < n:
            print(f'Counting up{x}')
            yield
            x += 1

    timeout = Event()

    scheduler.new_task('countup', countdown(10))
    scheduler.new_task('countup2', countdown(5))
    scheduler.new_task('timer', timer_task(10, timeout))
    scheduler.new_task('countdown', countup(15))
    scheduler.run()

    timeout.wait()

    log.log(f'countup metadata {scheduler.get_task_metadata("countup")}')
    log.log(f'countup2 metadata {scheduler.get_task_metadata("countup2")}')
    log.log(f'countdown metadata {scheduler.get_task_metadata("countdown")}')
    log.log(f'timer metadata {scheduler.get_task_metadata("timer")}')
