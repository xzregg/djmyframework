# -*- coding: utf-8 -*-
# @Time    : 2019-09-02 17:57
# @Author  : xzr
# @File    : celery_app
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : 

from __future__ import absolute_import, unicode_literals

import os
import time

import ulid as ulid
from celery import Celery, Task
from celery import Celery, Task
from celery.result import AsyncResult
from config.celery_schedule import BEAT_SCHEDULE
from raven.contrib.celery import register_logger_signal, register_signal
from threading import local

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
from django.db.transaction import on_commit
from framework.utils import capture_exception


request_context = local()
request_context.headers = {}


def get_request_context():
    return getattr(request_context, 'headers', {})


def set_request_context(**kwargs):
    try:
        headers = get_request_context()
        headers.update(kwargs)
        request_context.headers = headers
    except Exception as e:
        capture_exception()


def destroy_request_context():
    get_request_context().clear()
def commit_task(task_func):
    """
    发送任务时出错重试 3 次提交
    """
    replay_num = 3
    for i in range(replay_num):
        try:
            task_func()
            break
        except Exception as e:
            time.sleep(0.01)
            if i >= replay_num - 1:
                capture_exception()


class MyTask(Task):
    """等任务事务提交后再执行异步任务"""

    def apply_async(self, *args, **kwargs):  # 有些任务需要返回 task_result 所以就不全改了
        task_id = str(ulid.new())
        kwargs['task_id'] = task_id
        kwargs['headers'] = get_request_context()
        on_commit(lambda: commit_task(lambda: super(MyTask, self).apply_async(*args, **kwargs)))
        result = (kwargs.get('result_cls', None) or self.AsyncResult)(task_id)
        result.ignored = kwargs.get('ignored_result', False)
        return result



class MyCelery(Celery):
    task_cls = MyTask

    def send_task(self, *args, **kwargs):
        return super().send_task(*args, **kwargs)

    # def on_configure(self):
    #     client = raven.Client(settings.SENTRY_DSN)
    #     # register a custom filter to filter out duplicate logs
    #     register_logger_signal(client)
    #     # hook into the Celery error handle
    #     register_signal(client)

    def get_result(self, task_id) -> AsyncResult:
        result = self.AsyncResult(task_id)
        try:
            result.info
        except Exception as e:
            result = self.AsyncResult(task_id)
        return result

app = MyCelery('celery_app')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
    return self.request.id


# 设置任务路由 启动 celery 进程 用 -Q myadmin
# app.conf.task_routes = {'myadmin.tasks.*': {'queue': 'myadmin'}}
app.conf.task_routes = {}

app.conf.update(
        CELERY_REDIS_MAX_CONNECTIONS=12,
        CELERY_POOL_LIMIT=13,
        CELERY_TASK_SERIALIZER='pickle',
        CELERY_RESULT_SERIALIZER='pickle',
        CELERY_ACCEPT_CONTENT=['json', 'pickle'],
        CELERY_ENABLE_UTC=False,
        CELERY_TIMEZONE='Asia/Shanghai',
        CELERY_TRANSPORT_OPTIONS={
                'max_connections': 40,
        },
        CELERYBEAT_SCHEDULE=BEAT_SCHEDULE,
)



def update_state(self: Task, progress_num=0, total_progress_num=None, update_step=4):
    """
    更新异步任务的进度
    @param self: celery 任务，通过装饰器 bing=True
    @param progress_num: 当前的进度，可以是百分比，可以是某个或循环值如 30(progress_num)/200(total_progress_num) * 100 = 15%
    @param total_progress_num: 总数量
    @param update_step: 更新间隔
    @return:
    """
    if self.request.id:
        if not hasattr(self.request, 'total_progress_num') and total_progress_num:
            self.request.total_progress_num = total_progress_num
        if hasattr(self.request, 'total_progress_num'):
            progress_num = progress_num / self.request.total_progress_num * 100
        progress_num = min(progress_num, 100)
        last_progress_num = getattr(self.request,'last_progress_num', 0)
        # 最多每百分之1更新一次，每个任务最多更新 100 次
        if (progress_num - last_progress_num > 1) or progress_num == 100:
            self.request.last_progress_num = progress_num
            self.update_state(state="PROGRESS", meta={'progress': int(progress_num)})


@app.task(bind=True)
def debug_task_export(self: Task):
    print('Request: {0!r}'.format(self.request))
    # time.sleep(30)
    return '123'


@app.task(bind=True)
def test(self: Task, a, b, v=False):
    print(a + b)
    if v:
        raise 1
    return a + b