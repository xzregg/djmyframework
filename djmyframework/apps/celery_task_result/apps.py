from django.apps import AppConfig

from framework.translation import _


class CeleryTaskResultConfig(AppConfig):
    name = 'celery_task_result'
    verbose_name = _('Celery 任务结果')
