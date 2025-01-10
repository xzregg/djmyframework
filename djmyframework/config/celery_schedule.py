# -*- coding: utf-8 -*-
# @Time    : 2025/1/10 11:17 
# @Author  : xzr
# @File    : celery_schedule.py
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    :

from celery.schedules import crontab

BEAT_SCHEDULE = {
        'release-card-subsidy-everyday': {
                'task'    : 'card_service.tasks.card_subsidy.auto_release_card_subsidy',
                'schedule': crontab(minute=1, hour=0),
        },
}
