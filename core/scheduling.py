from collections import deque
from time import time
from threading import Event


class TaskEvent:

    def __init__(self):
        self.event = Event()


class TaskTimer:

    def __init__(self):
        self.timeout = 0
        self.ts = 0
        self.te = 0


class Task:

    def __init__(self, name, ret_queue):
        self.name = name
        self.ret_queue = ret_queue
        self.dependency = None
        self.status = 'idle'
        self.event = None
        self.timer = None

    def set_dependency(self, dependency):
        self.dependency = dependency

    def set_task_event(self, event: TaskEvent):
        self.event = event

    def set_task_timer(self, timer: TaskTimer):
        self.timer = timer


class Scheduler:

    def __init__(self):
        self.jobs = deque()
        self.tasks = {}

    def _append_job(self, name, func):
        self.jobs.append((name, func))

    def spawn_task(self, name: str, func, ret_queue=list()):
        self._append_job(name, func)
        self.tasks[name] = Task(name, ret_queue)

    def set_dependency(self, name: str, dependency: str):
        self.tasks[name].set_dependency(self.tasks[dependency])
        self.tasks[name].status = 'wait_task'

    def wait_event(self, name: str, event: TaskEvent):
        event.ts = time()
        self.tasks[name].set_task_event(event)
        self.tasks[name].status = 'wait_event'

    def wait_timer(self, name: str, timer: TaskTimer):
        timer.ts = time()
        self.tasks[name].set_task_timer(timer)
        self.tasks[name].status = 'wait_timer'

    def run(self):
        while self.jobs:
            # pop next job
            job_name, job = self.jobs.popleft()
            task = self.tasks[job_name]

            # check if job is waiting for other jobs
            if task.status == 'wait_task' and task.dependency.status == 'finished':
                task.status = 'idle'

            # check if job is waiting a event
            if task.status == 'wait_event' and task.event.event.isSet():
                task.status = 'idle'

            # check if a job is waiting a timer
            if task.status == 'wait_timer':
                now_time = time()
                task.timer.te += now_time - task.timer.ts
                task.timer.ts = now_time
                if task.timer.te > task.timer.timeout:
                    task.status = 'idle'

            if task.status == 'idle':
                try:
                    task.status = 'running'
                    ret = next(job)
                    if ret:
                        task.ret_queue.append(ret)
                    if task.status == 'running':
                        task.status = 'idle'
                    self._append_job(job_name, job)
                except StopIteration:
                    task.status = 'finished'
            else:
                self._append_job(job_name, job)


scheduler = Scheduler()


if __name__ == '__main__':

    class Tester:

        def __init__(self):
            self.evt = TaskEvent()
            self.timer_ = TaskTimer()
            self.timer_.timeout = 3
            self.ret_queue = []

            scheduler.spawn_task('task_wait_event', self.task_wait_event())
            scheduler.spawn_task('task_dependency', self.task_dependency())
            scheduler.spawn_task('task_wait_timer', self.task_wait_timer())
            scheduler.spawn_task('task_with_return', self.task_with_return(), ret_queue=self.ret_queue)

        def task_set_event(self):
            n = 10
            while n > 0:
                print(f'Running set event task {n}')
                yield
                n -= 1
            self.evt.event.set()

        def task_wait_event(self):
            n = 5
            scheduler.wait_event('task_wait_event', self.evt)
            yield
            while n > 0:
                print(f'Running wait event {n}')
                yield
                n -= 1

        def task_dependency(self):
            n = 5
            scheduler.set_dependency('task_dependency', 'task_wait_event')
            yield
            while n > 0:
                print(f'Running dependency {n}')
                yield
                n -= 1

        def task_wait_timer(self):
            n = 5
            scheduler.wait_timer('task_wait_timer', self.timer_)
            yield
            while n > 0:
                print(f'Running wait timer {n}')
                yield
                n -= 1

        def task_with_return(self):
            n = 5
            while n > 0:
                print(f'Running with return {n}')
                yield
                n -= 1
            yield 200


    tester = Tester()

    scheduler.spawn_task('task_set_event', tester.task_set_event())
    scheduler.run()
    print(tester.ret_queue)
