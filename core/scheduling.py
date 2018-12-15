from collections import deque
from time import time
from dataclasses import dataclass
from core.log import Log, LogLevel
from typing import List
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


class Scheduler:

    def __init__(self):
        self.tasks = deque()
        self.tasks_dependency = {}
        self.tasks_status = {}

    def new_task(self, name: str):
        def wrap(func):
            self.tasks.append((name, func()))
            self.tasks_status[name] = 'running'
            return func
        return wrap

    def add_dependency(self, name: str, dependency: str):
        self.tasks_dependency[name] = dependency

    def run(self):
        while self.tasks:
            # pop next task
            task_name, task = self.tasks.popleft()

            # check dependencies
            if task_name in self.tasks_dependency:
                dependency = self.tasks_dependency[task_name]
                if self.tasks_status[dependency] == 'running':
                    self.tasks.append((task_name, task))
                    continue

            try:
                log.dbg(f'Start task')
                next(task)
                log.dbg(f'Yield task')
                self.tasks.append((task_name, task))
            except StopIteration:
                self.tasks_status[task_name] = 'finished'


scheduler = Scheduler()


if __name__ == '__main__':

    @scheduler.new_task('task_in')
    def task_in():
        n = 10
        while n > 0:
            print(f'Runing in task {n}')
            yield
            n -= 1

    @scheduler.new_task('task_out')
    def task_out():
        n = 5
        while n > 0:
            print(f'Task out executing {n}')
            scheduler.add_dependency('task_out', 'task_in')
            yield
            n -= 1

    scheduler.run()
