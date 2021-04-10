# -*- coding: utf-8 -*-
# @Time    : 2021-03-12 14:44
# @Author  : xzr
# @File    : __init__
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : 

from config.celery_app import app as celery_app

__all__ = ('celery_app',)