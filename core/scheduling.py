import sys
sys.path.append('/home/matheuswhite/Documentos/bluebees/')

from collections import deque
from time import time
from threading import Event
from typing import List
from core.path import Path
from core.utils import threaded

"""
WARNING

Please don't use method in the region 'Scheduler Helpers'
This methods are used in scheduler and any changes outside scheduler will cause a program crash
"""

class Timer:

    def __init__(self):
        self._timeout = 0
        self._is_over = False
        self._is_enable = False
        self._ts = 0
        self._te = 0

    @property
    def is_enable(self):
        return self._is_enable

    @is_enable.setter
    def is_enable(self, value):
        self._is_enable = value

    @property
    def is_over(self):
        return self._is_over

    @property
    def elapsed_time(self):
        return self._te

    @property
    def start_time(self):
        return self._ts

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value
        self.start()

    def start(self):
        self._is_over = False
        self._ts = time()
        self._te = 0
        self._is_enable = True

    def tick(self):
        now_time = time()
        self._te += now_time - self._ts
        self._ts = now_time
        if self._te >= self.timeout:
            self._is_over = True

class TaskError(Exception):
    
    def __init__(self, errno: int, message: str):
        self.errno = errno
        self.message = message

class Task:

    def __init__(self, name: str):
        self._name = name + '/'
        self._results = []
        self._errors = []
        self._event = None
        self._timer = Timer()

        self._status = 'idle'
        self._task_dependency = None
        self._last_results_len = len(self._results)

    #region Properties
    @property
    def name(self):
        return self._name

    @property
    def order(self):
        parts = self._name.split('/')
        if parts[1] != '':
            return parts[1]

    @property
    def results(self):
        return self._results.copy()

    @property
    def errors(self):
        return self._errors.copy()

    @property
    def status(self):
        return self._status

    @property
    def timer(self):
        return self._timer

    @property
    def event(self):
        return self._event

    @property
    def job(self):
        return self._job

    @job.setter
    def job(self, value):
        self._job = value
    #endregion

    #region Private
    def _tick_timer(self):
        if self.timer.is_enable:
            self.timer.tick()
            if self.timer.is_over:
                self._status = 'idle'
                self.timer.is_enable = False
    #endregion

    #region Public
    def get_first_result(self):
        if len(self._results) > 0:
            return self._results[0]
    
    def get_last_result(self):
        length = len(self._results)
        if length > 0:
            return self._results[length - 1]

    def has_error(self):
        return len(self._errors) > 0

    def wait_finish(self, task, timeout=None):
        if timeout:
            self._timer.timeout = timeout
        self._task_dependency = task
        self._status = 'wait_finish'

    def wait_result(self, task, timeout=None):
        if timeout:
            self._timer.timeout = timeout
        self._task_dependency = task
        self._status = 'wait_result'

    def wait_event(self, event: Event, timeout=None):
        if timeout:
            self._timer.timeout = timeout
        self._event = event
        self._status = 'wait_event'

    def wait_timer(self, timeout: None):
        self._timer.timeout = timeout
        self._status = 'wait_timer'
    #endregion

    #region Scheduler Helpers
    @order.setter
    def order(self, value: int):
        self._name = self._name.split('/')[0] + f'/{value}'

    @property
    def last_results_len(self):
        return self._last_results_len

    @last_results_len.setter
    def last_results_len(self, value):
        self._last_results_len = value

    def change_state(self):
        # check if wait is timeout
        if self.status in ['wait_finish', 'wait_result', 'wait_event', 'wait_timer']:
            self._tick_timer()

        # check if job is waiting for other jobs finish
        if self.status == 'wait_finish':
            if self._task_dependency.status == 'finished' or self._task_dependency.status == 'error':
                self._status = 'idle'

        # check if job is waiting for other jobs result
        if self.status == 'wait_result':
            if self._task_dependency.status == 'error':
                self._status = 'idle'
            else:
                results_len = len(self._task_dependency.results)
                if results_len > 0 and self._task_dependency.last_results_len != results_len:
                    self._task_dependency.last_results_len = results_len
                    self._status = 'idle'

        # check if job is waiting a event
        if self.status == 'wait_event' and self.event.isSet():
            self._status = 'idle'

        if self.status == 'idle':
            try:
                self._status = 'running'
                ret = next(self.job)
                if ret is not None:
                    self._results.append(ret)
                if self.status == 'running':
                    self._status = 'idle'
            except StopIteration:
                self._status = 'finished'
            except TaskError as error:
                self._errors.append(error)
                self._status = 'error'
    #endregion

class Scheduler:

    def __init__(self):
        self._jobs = deque()
        self._tasks = Path()

        self.is_alive = True

    #region Private
    def _append_job(self, task_name: str, job):
        self._jobs.append((task_name, job))
    #endregion

    #region Public
    def kill(self):
        self.is_alive = False

    def spawn_task(self, func, *args, **kwargs) -> Task:
        task_base_name = func.__name__
        task = Task(task_base_name)
        task.job = func(task, *args, **kwargs)
        task_order = self._tasks.add(task_base_name, task)
        task.order = task_order

        self._append_job(task.name, task.job)

        return task

    # @threaded
    def run(self):
        while self.is_alive:
            # check is has job in the queue
            if len(self._jobs) <= 0:
                continue

            # pop next job
            task_name, job = self._jobs.popleft()
            task = self._tasks.get_val(task_name)

            # change task state and execute if possible
            task.change_state()

            # if the task is not finished, then append to jobs queue
            if task.status != 'finished' and task.status != 'error':
                self._append_job(task_name, job)
    #endregion

scheduler = Scheduler()


if __name__ == '__main__':

    class Tester:

        def __init__(self):
            self.kill_event = Event()

            self.kill_at_task = scheduler.spawn_task(self.kill_at_t, time=25)
            self.wait_timer_task = scheduler.spawn_task(self.wait_timer_t)
            self.wait_result_task = scheduler.spawn_task(self.wait_result_t)
            self.wait_event_task = scheduler.spawn_task(self.wait_event_t)
            self.wait_finish_task = scheduler.spawn_task(self.wait_finish_t)

        def wait_timer_t(self, self_task: Task):
            while not self.kill_event.isSet():
                print('[1] waiting timer')
                self.wait_timer_task.wait_timer(timeout=3)
                yield
                print('[1] timeout')
                yield self.wait_timer_task.timer.elapsed_time

        def wait_result_t(self, self_task: Task):
            while not self.kill_event.isSet():
                print('[2] waiting result')
                self.wait_result_task.wait_result(self.wait_timer_task, timeout=4)
                yield
                print(f'[2] Timer elapsed time values: {self.wait_timer_task.results}')

        def kill_at_t(self, self_task: Task, time: int):
            print(f'time: {time}')
            self.kill_at_task.wait_timer(timeout=time)
            yield
            print('[3] kill all')
            self.kill_event.set()

        def wait_event_t(self, self_task: Task):
            print('[4] wait event')
            self.wait_event_task.wait_event(self.kill_event, timeout=30)
            yield
            print('[4] wait event finish')

        def wait_finish_t(self, self_task: Task):
            print('[5] waiting finish')
            self.wait_finish_task.wait_finish(self.wait_event_task, timeout=31)
            yield
            print('[5] wait finish done')
            scheduler.kill()


    tester = Tester()
    scheduler.run()
