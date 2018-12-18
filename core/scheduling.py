from collections import deque
from time import time
from threading import Event


class Timer:

    def __init__(self, timeout: int):
        self.timeout = timeout
        self.ts = 0
        self.te = 0


class Task:

    def __init__(self, name, ret_queue):
        self.name = name
        self.ret_queue = ret_queue
        self.task_dependency = None
        self.last_ret_queue_len = len(ret_queue)
        self.status = 'idle'
        self.event = None
        self.timer = None


class Scheduler:

    def __init__(self):
        self.jobs = deque()
        self.tasks = {}

    def _append_job(self, name, func):
        self.jobs.append((name, func))

    def spawn_task(self, name: str, func, ret_queue=list()):
        self._append_job(name, func)
        self.tasks[name] = Task(name, ret_queue)

    def wait_finish(self, invoker_name: str, task_name: str, timer=None):
        task = self.tasks[invoker_name]
        if timer:
            task.timer = timer
            task.timer.ts = time()
        task.task_dependency = self.tasks[task_name]
        task.status = 'wait_finish'

    def wait_result(self, invoker_name: str, task_name: str, timer=None):
        task = self.tasks[invoker_name]
        if timer:
            task.timer = timer
            task.timer.ts = time()
        task.task_dependency = self.tasks[task_name]
        task.status = 'wait_result'

    def wait_event(self, invoker_name: str, event: Event, timer=None):
        task = self.tasks[invoker_name]
        if timer:
            task.timer = timer
            task.timer.ts = time()
        task.event = event
        task.status = 'wait_event'

    def wait_timer(self, invoker_name: str, timer: Timer):
        task = self.tasks[invoker_name]
        task.timer = timer
        task.timer.ts = time()
        task.status = 'wait_timer'

    def _tick_timer(self, task):
        if task.timer:
            now_time = time()
            task.timer.te += now_time - task.timer.ts
            task.timer.ts = now_time
            if task.timer.te >= task.timer.timeout:
                task.status = 'idle'

    def run(self):
        while self.jobs:
            # pop next job
            job_name, job = self.jobs.popleft()
            task = self.tasks[job_name]

            # check if wait is timeout
            if task.status in ['wait_finish', 'wait_result', 'wait_event', 'wait_timer']:
                self._tick_timer(task)

            # check if job is waiting for other jobs finish
            if task.status == 'wait_finish' and task.task_dependency.status == 'finished':
                task.status = 'idle'

            # check if job is waiting for other jobs result
            if task.status == 'wait_result':
                ret_queue_len = len(task.task_dependency.ret_queue)
                if ret_queue_len > 0 and task.task_dependency.last_ret_queue_len != ret_queue_len:
                    task.task_dependency.last_ret_queue_len = ret_queue_len
                    task.status = 'idle'

            # check if job is waiting a event
            if task.status == 'wait_event' and task.event.isSet():
                task.status = 'idle'

            if task.status == 'idle':
                try:
                    task.status = 'running'
                    ret = next(job)
                    if ret is not None:
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
            self.kill_event = Event()
            self.timer_ = Timer(timeout=3)
            self.ret_queue = []

            scheduler.spawn_task('kill_at_t', self.kill_at_t(time=25))
            scheduler.spawn_task('wait_timer_t', self.wait_timer_t(), self.ret_queue)
            scheduler.spawn_task('wait_result_t', self.wait_result_t())
            scheduler.spawn_task('wait_event_t', self.wait_event_t())
            scheduler.spawn_task('wait_finish_t', self.wait_finish_t())

        def wait_timer_t(self):
            while not self.kill_event.isSet():
                print('[1] waiting timer')
                scheduler.wait_timer('wait_timer_t', self.timer_)
                yield
                print('[1] timeout')
                yield self.timer_.te
                self.timer_ = Timer(timeout=3)

        def wait_result_t(self):
            while not self.kill_event.isSet():
                print('[2] waiting result')
                scheduler.wait_result('wait_result_t', 'wait_timer_t', Timer(timeout=4))
                yield
                print(f'[2] Timer te values: {self.ret_queue}')

        def kill_at_t(self, time: int):
            kill_timer = Timer(time)
            scheduler.wait_timer('kill_at_t', kill_timer)
            yield
            print('[3] kill all')
            self.kill_event.set()

        def wait_event_t(self):
            print('[4] wait event')
            scheduler.wait_event('wait_event_t', self.kill_event, Timer(timeout=30))
            yield
            print('[4] wait event finish')

        def wait_finish_t(self):
            print('[5] waiting finish')
            scheduler.wait_finish('wait_finish_t', 'wait_event_t', Timer(timeout=31))
            yield
            print('[5] wait finish done')


    tester = Tester()
    scheduler.run()
